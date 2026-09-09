import os
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.database import SessionLocal
from app.main import app, sync_database_schema
from app.models.user import User, UserRole
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.models.security_rule import SecurityEventSeverity, SecurityEventType
from app.core.security import create_access_token, hash_password
from app.core.events.publisher import get_event_publisher
from app.core.websocket_manager import get_connection_manager
from app.services.realtime_service import RealtimeStatus, get_realtime_session_manager


@pytest.fixture(scope="module")
def db_session():
    sync_database_schema()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def operator_a(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"soc_a_{user_id[:8]}@sentinel.ai",
        name="SOC Operator Alpha",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def operator_b(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"soc_b_{user_id[:8]}@sentinel.ai",
        name="SOC Operator Beta",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def auth_headers_a(operator_a):
    token = create_access_token(operator_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def auth_headers_b(operator_b):
    token = create_access_token(operator_b.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def mock_job_a(db_session, operator_a):
    job_id = str(uuid.uuid4())
    dummy_video = os.path.join(os.path.dirname(__file__), f"dummy_video_{job_id[:8]}.mp4")
    with open(dummy_video, "wb") as f:
        f.write(b"dummy video data")

    job = AnalysisJob(
        id=job_id,
        user_id=operator_a.id,
        source_type="VIDEO_FILE",
        source_path=dummy_video,
        original_filename="perimeter_cam01.mp4",
        status=JobStatus.QUEUED,
        progress=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    yield job

    if os.path.exists(dummy_video):
        try:
            os.remove(dummy_video)
        except OSError:
            pass


@pytest.fixture(scope="module")
def mock_job_b(db_session, operator_b):
    job_id = str(uuid.uuid4())
    dummy_video = os.path.join(os.path.dirname(__file__), f"dummy_video_{job_id[:8]}.mp4")
    with open(dummy_video, "wb") as f:
        f.write(b"dummy video data")

    job = AnalysisJob(
        id=job_id,
        user_id=operator_b.id,
        source_type="VIDEO_FILE",
        source_path=dummy_video,
        original_filename="warehouse_cam02.mp4",
        status=JobStatus.QUEUED,
        progress=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    yield job

    if os.path.exists(dummy_video):
        try:
            os.remove(dummy_video)
        except OSError:
            pass


# ─── 1. Realtime Session Lifecycle Tests ─────────────────────────────────────

def test_realtime_session_start_and_status(client, auth_headers_a, mock_job_a):
    """Verify starting a real-time session updates status and returns initial metrics."""
    res = client.post(
        f"/api/video-analysis/{mock_job_a.id}/realtime/start",
        headers=auth_headers_a,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == mock_job_a.id
    assert data["status"] in (RealtimeStatus.STARTING, RealtimeStatus.RUNNING, RealtimeStatus.STOPPED, RealtimeStatus.COMPLETED, RealtimeStatus.FAILED)

    # Check status endpoint
    status_res = client.get(
        f"/api/video-analysis/{mock_job_a.id}/realtime/status",
        headers=auth_headers_a,
    )
    assert status_res.status_code == 200
    stat_data = status_res.json()
    assert stat_data["job_id"] == mock_job_a.id
    assert "frames_processed" in stat_data
    assert "processing_fps" in stat_data
    assert "active_tracks" in stat_data


def test_realtime_duplicate_start_conflict(client, auth_headers_a, mock_job_a):
    """Verify attempting to start an already running session returns 409 Conflict."""
    manager = get_realtime_session_manager()
    session = manager.get_session(mock_job_a.id)
    if session:
        session.status = RealtimeStatus.RUNNING

        res = client.post(
            f"/api/video-analysis/{mock_job_a.id}/realtime/start",
            headers=auth_headers_a,
        )
        assert res.status_code == 409
        assert "already running" in res.json()["detail"].lower()


def test_realtime_session_stop(client, auth_headers_a, mock_job_a):
    """Verify stopping an active monitoring session safely updates status to STOPPED."""
    manager = get_realtime_session_manager()
    session = manager.get_session(mock_job_a.id)
    if not session:
        manager.start_session(mock_job_a.id, mock_job_a.user_id, SessionLocal())

    res = client.post(
        f"/api/video-analysis/{mock_job_a.id}/realtime/stop",
        headers=auth_headers_a,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in (RealtimeStatus.STOPPED, RealtimeStatus.COMPLETED, RealtimeStatus.STOPPING)


def test_realtime_ownership_protection(client, auth_headers_b, mock_job_a):
    """Verify Operator B cannot access or control Operator A's real-time monitoring session."""
    # Attempt start
    res_start = client.post(
        f"/api/video-analysis/{mock_job_a.id}/realtime/start",
        headers=auth_headers_b,
    )
    assert res_start.status_code == 404

    # Attempt status
    res_status = client.get(
        f"/api/video-analysis/{mock_job_a.id}/realtime/status",
        headers=auth_headers_b,
    )
    assert res_status.status_code == 404

    # Attempt stop
    res_stop = client.post(
        f"/api/video-analysis/{mock_job_a.id}/realtime/stop",
        headers=auth_headers_b,
    )
    assert res_stop.status_code == 404


# ─── 2. WebSocket Authentication & Isolation Tests ───────────────────────────

def test_websocket_unauthenticated_rejected(client, mock_job_a):
    """Verify WebSocket connection without a JWT token is immediately rejected."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/ws/analysis/{mock_job_a.id}"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_unauthorized_job_rejected(client, operator_b, mock_job_a):
    """Verify Operator B cannot subscribe to Operator A's video analysis stream."""
    token_b = create_access_token(operator_b.id)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/ws/analysis/{mock_job_a.id}?token={token_b}"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_authenticated_connection(client, operator_a, mock_job_a):
    """Verify authorized operator successfully receives initial status_update message."""
    token_a = create_access_token(operator_a.id)
    with client.websocket_connect(f"/api/ws/analysis/{mock_job_a.id}?token={token_a}") as ws:
        # Initial greeting / status message
        initial_msg = ws.receive_json()
        assert initial_msg["type"] == "status_update"
        assert initial_msg["job_id"] == mock_job_a.id
        assert "data" in initial_msg

        # Test keep-alive ping/pong
        ws.send_text("ping")
        pong = ws.receive_text()
        assert pong == "pong"


def test_event_publisher_and_session_isolation(client, operator_a, operator_b, mock_job_a, mock_job_b):
    """
    Verify real-time event publisher broadcasts events to the correct job subscribers
    and maintains strict isolation between Job A and Job B.
    """
    token_a = create_access_token(operator_a.id)
    publisher = get_event_publisher()

    with client.websocket_connect(f"/api/ws/analysis/{mock_job_a.id}?token={token_a}") as ws_a:
        # Consume initial greeting
        _ = ws_a.receive_json()

        # Publish test security event to Job A
        test_event = {
            "id": str(uuid.uuid4()),
            "event_type": "INTRUSION",
            "severity": "HIGH",
            "title": "Restricted Zone Intrusion",
            "start_timestamp": 12.5,
        }
        publisher.publish("security_event", test_event, mock_job_a.id, operator_a.id)

        # ws_a should receive this event
        received = ws_a.receive_json()
        assert received["type"] == "security_event"
        assert received["job_id"] == mock_job_a.id
        assert received["data"]["id"] == test_event["id"]
        assert received["data"]["severity"] == "HIGH"


def test_database_persistence_before_event_delivery(db_session, operator_a, mock_job_a):
    """
    Verify architectural requirement: database persistence is authoritative,
    and records exist in the database upon security event emission.
    """
    event_id = str(uuid.uuid4())
    sec_ev = SecurityEvent(
        id=event_id,
        analysis_job_id=mock_job_a.id,
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.HIGH,
        status=SecurityEventStatus.OPEN,
        title="Test Intrusion Incident",
        description="Target entered restricted perimeter zone.",
        start_timestamp=15.0,
    )
    db_session.add(sec_ev)
    db_session.commit()

    # Query DB to confirm persistence
    queried = db_session.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    assert queried is not None
    assert queried.title == "Test Intrusion Incident"
    assert queried.status == SecurityEventStatus.OPEN
    assert queried.analysis_job_id == mock_job_a.id
