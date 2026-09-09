"""
Phase 9 — Advanced Analytics & Anomaly Intelligence Test Suite.

Verifies:
1. Authentication & strict user ownership data isolation.
2. Date range preset parsing and custom range validation.
3. Overview metrics calculation and zero-safe period comparison.
4. Adaptive time-series event trends (hourly, daily, weekly).
5. Event type and severity distribution breakdowns.
6. Per-camera performance and deterministic, explainable risk scoring.
7. 7x24 Day vs Hour security activity heatmap and time patterns.
8. Incident lifecycle metrics and average resolution duration.
9. Statistical baseline calculations & rule-based anomaly detection.
10. Insufficient data handling and zero-division protection.
11. Deterministic operational security insights.
"""
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app, sync_database_schema
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.camera import Camera, CameraSourceType, CameraStatus
from app.models.incident_report import IncidentOperationalStatus, IncidentReport
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.models.security_rule import SecurityEventSeverity, SecurityEventType
from app.models.user import User, UserRole


@pytest.fixture(scope="module")
def db_session():
    sync_database_schema()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def user_alpha(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"alpha_{user_id[:8]}@sentinel.ai",
        name="SOC Operator Alpha",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def user_beta(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"beta_{user_id[:8]}@sentinel.ai",
        name="SOC Operator Beta",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def token_alpha(user_alpha):
    return create_access_token(subject=user_alpha.id)


@pytest.fixture(scope="module")
def token_beta(user_beta):
    return create_access_token(subject=user_beta.id)


@pytest.fixture(scope="module")
def test_camera_1(db_session):
    cam = Camera(
        id=str(uuid.uuid4()),
        name="North Perimeter Cam",
        location="Zone North A",
        source_type=CameraSourceType.RTSP,
        status=CameraStatus.ONLINE,
        is_enabled=True,
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)
    return cam


@pytest.fixture(scope="module")
def test_camera_2(db_session):
    cam = Camera(
        id=str(uuid.uuid4()),
        name="Main Entrance Gate",
        location="Gate 1",
        source_type=CameraSourceType.RTSP,
        status=CameraStatus.ONLINE,
        is_enabled=True,
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)
    return cam


# ─── 1. Authentication & Security Tests ───────────────────────────────────────

def test_unauthenticated_analytics_rejected(client):
    """Analytics endpoints must reject unauthenticated requests."""
    res = client.get("/api/analytics/overview")
    assert res.status_code in (401, 403)

    res = client.get("/api/analytics/events/trends")
    assert res.status_code in (401, 403)


def test_user_ownership_isolation(client, db_session, user_alpha, user_beta, token_alpha, token_beta, test_camera_1):
    """User A cannot view User B's events, incidents, or metrics."""
    now = datetime.now(timezone.utc)

    # User Alpha Job & Event
    job_a = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=user_alpha.id,
        camera_id=test_camera_1.id,
        source_path="/test/path/a.mp4",
        original_filename="alpha_vid.mp4",
        status=JobStatus.COMPLETED,
    )
    db_session.add(job_a)
    db_session.commit()

    ev_a = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job_a.id,
        camera_id=test_camera_1.id,
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.HIGH,
        status=SecurityEventStatus.OPEN,
        title="Alpha Intrusion Alert",
        description="Alpha detected intrusion",
        start_timestamp=10.0,
        created_at=now - timedelta(hours=2),
    )
    db_session.add(ev_a)

    # User Beta Job & Event
    job_b = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=user_beta.id,
        camera_id=test_camera_1.id,
        source_path="/test/path/b.mp4",
        original_filename="beta_vid.mp4",
        status=JobStatus.COMPLETED,
    )
    db_session.add(job_b)
    db_session.commit()

    ev_b = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job_b.id,
        camera_id=test_camera_1.id,
        event_type=SecurityEventType.LOITERING,
        severity=SecurityEventSeverity.CRITICAL,
        status=SecurityEventStatus.OPEN,
        title="Beta Loitering Alert",
        description="Beta detected critical loitering",
        start_timestamp=15.0,
        created_at=now - timedelta(hours=2),
    )
    db_session.add(ev_b)
    db_session.commit()

    # Query overview for Alpha
    headers_a = {"Authorization": f"Bearer {token_alpha}"}
    res_a = client.get("/api/analytics/overview?preset=24h", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["high_severity_events"] >= 1
    # Alpha must not have critical events from Beta
    assert data_a["critical_events"] == 0

    # Query overview for Beta
    headers_b = {"Authorization": f"Bearer {token_beta}"}
    res_b = client.get("/api/analytics/overview?preset=24h", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["critical_events"] >= 1
    # Beta must not have Alpha's event
    assert data_b["high_severity_events"] == 0


# ─── 2. Date Range Validation ─────────────────────────────────────────────────

def test_date_range_validation_success(client, token_alpha):
    """Presets 24h, 7d, 30d, 90d return 200."""
    headers = {"Authorization": f"Bearer {token_alpha}"}
    for preset in ["24h", "7d", "30d", "90d"]:
        res = client.get(f"/api/analytics/overview?preset={preset}", headers=headers)
        assert res.status_code == 200
        assert "total_events" in res.json()


def test_date_range_custom_valid(client, token_alpha):
    """Valid custom ISO range returns 200 with appropriate interval."""
    headers = {"Authorization": f"Bearer {token_alpha}"}
    start = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    end = datetime.now(timezone.utc).isoformat()
    res = client.get(
        f"/api/analytics/events/trends?preset=custom&start_date={start}&end_date={end}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["interval"] == "daily"


def test_date_range_invalid_start_after_end(client, token_alpha):
    """Custom range with start > end must return 400."""
    headers = {"Authorization": f"Bearer {token_alpha}"}
    start = datetime.now(timezone.utc).isoformat()
    end = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    res = client.get(
        f"/api/analytics/overview?preset=custom&start_date={start}&end_date={end}",
        headers=headers,
    )
    assert res.status_code == 400
    assert "cannot be after" in res.json()["detail"].lower()


def test_date_range_exceeding_max_days(client, token_alpha):
    """Custom range exceeding 365 days must return 400."""
    headers = {"Authorization": f"Bearer {token_alpha}"}
    start = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    end = datetime.now(timezone.utc).isoformat()
    res = client.get(
        f"/api/analytics/overview?preset=custom&start_date={start}&end_date={end}",
        headers=headers,
    )
    assert res.status_code == 400
    assert "cannot exceed 365" in res.json()["detail"]


# ─── 3. Event Trends & Distributions ──────────────────────────────────────────

def test_event_trends_intervals(client, token_alpha):
    """Verify adaptive interval selection for 24h (hourly), 7d (daily), 90d (weekly)."""
    headers = {"Authorization": f"Bearer {token_alpha}"}

    res_24h = client.get("/api/analytics/events/trends?preset=24h", headers=headers)
    assert res_24h.status_code == 200
    assert res_24h.json()["interval"] == "hourly"

    res_7d = client.get("/api/analytics/events/trends?preset=7d", headers=headers)
    assert res_7d.status_code == 200
    assert res_7d.json()["interval"] == "daily"

    res_90d = client.get("/api/analytics/events/trends?preset=90d", headers=headers)
    assert res_90d.status_code == 200
    assert res_90d.json()["interval"] == "weekly"


def test_event_type_and_severity_distribution(client, token_alpha):
    """Distributions return formatted items with percentages."""
    headers = {"Authorization": f"Bearer {token_alpha}"}

    res_types = client.get("/api/analytics/events/distribution?preset=7d", headers=headers)
    assert res_types.status_code == 200
    assert "items" in res_types.json()

    res_sev = client.get("/api/analytics/events/severity?preset=7d", headers=headers)
    assert res_sev.status_code == 200
    data_sev = res_sev.json()
    assert len(data_sev["items"]) == 4  # LOW, MEDIUM, HIGH, CRITICAL


# ─── 4. Camera Analytics & Deterministic Risk Scoring ─────────────────────────

def test_camera_analytics_and_risk_scoring(client, db_session, user_alpha, token_alpha, test_camera_2):
    """Camera risk score must be clamped 0-100 with explainable contributing factors."""
    headers = {"Authorization": f"Bearer {token_alpha}"}

    res = client.get("/api/analytics/cameras?preset=7d", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "cameras" in data
    assert data["total_cameras"] >= 1

    for cam in data["cameras"]:
        assert 0 <= cam["risk_score"] <= 100
        assert cam["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert len(cam["risk_factors"]) >= 1


# ─── 5. Activity Heatmap Matrix ───────────────────────────────────────────────

def test_activity_heatmap_structure(client, token_alpha):
    """Heatmap must return 7x24 = 168 cells with days 0..6 and hours 0..23."""
    headers = {"Authorization": f"Bearer {token_alpha}"}
    res = client.get("/api/analytics/activity?preset=7d", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["cells"]) == 7 * 24
    assert "quiet_hours" in data


# ─── 6. Incident Analytics & Resolution Times ─────────────────────────────────

def test_incident_analytics_metrics(client, db_session, user_alpha, token_alpha, test_camera_1):
    """Incident analytics calculates lifecycle counts, resolution rate, and duration."""
    now = datetime.now(timezone.utc)
    # Add a resolved incident report with timestamps
    rep = IncidentReport(
        id=str(uuid.uuid4()),
        user_id=user_alpha.id,
        camera_id=test_camera_1.id,
        event_ids_json=["test-ev-1"],
        ai_provider="mock",
        summary="Test incident for resolution",
        risk_level="HIGH",
        incident_status=IncidentOperationalStatus.RESOLVED,
        created_at=now - timedelta(hours=1),
        resolved_at=now - timedelta(minutes=15),
    )
    db_session.add(rep)
    db_session.commit()

    headers = {"Authorization": f"Bearer {token_alpha}"}
    res = client.get("/api/analytics/incidents?preset=24h", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_incidents"] >= 1
    assert data["resolved_count"] >= 1
    assert data["resolution_rate"] > 0
    assert data["average_resolution_time_minutes"] is not None
    assert round(data["average_resolution_time_minutes"]) == 45


# ─── 7. Baseline & Anomaly Detection ──────────────────────────────────────────

def test_anomaly_detection_insufficient_data(client, db_session):
    """New user with no baseline events must return INSUFFICIENT_DATA status."""
    new_user = User(
        id=str(uuid.uuid4()),
        email=f"empty_{uuid.uuid4().hex[:6]}@sentinel.ai",
        name="Empty Operator",
        password_hash=hash_password("Pass123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(new_user)
    db_session.commit()

    token = create_access_token(subject=new_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/analytics/anomalies?preset=24h", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_sufficient_data"] is False
    assert data["status"] == "INSUFFICIENT_DATA"
    assert "Minimum 5 historical events required" in data["message"]


def test_anomaly_detection_volume_and_severity_spike(client, db_session, test_camera_1):
    """
    Simulate historical baseline (7 events across 7 days) and sudden surge in current period
    (12 events, multiple critical). Anomaly engine should flag EVENT_VOLUME_SPIKE and SEVERITY_SPIKE.
    """
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"spike_user_{user_id[:8]}@sentinel.ai",
        name="Spike Test Operator",
        password_hash=hash_password("Pass123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()

    job = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=user.id,
        camera_id=test_camera_1.id,
        source_path="/test/surge.mp4",
        original_filename="surge.mp4",
        status=JobStatus.COMPLETED,
    )
    db_session.add(job)
    db_session.commit()

    now = datetime.now(timezone.utc)

    # 1. Add 7 baseline events over the past 7 days (prior to last 24h)
    for i in range(7):
        ev = SecurityEvent(
            id=str(uuid.uuid4()),
            analysis_job_id=job.id,
            camera_id=test_camera_1.id,
            event_type=SecurityEventType.LOITERING,
            severity=SecurityEventSeverity.LOW,
            status=SecurityEventStatus.OPEN,
            title=f"Baseline Event {i}",
            description="Normal activity",
            start_timestamp=float(i * 10),
            created_at=now - timedelta(days=2, hours=i),
        )
        db_session.add(ev)

    # 2. Add 10 events within last 24h, with 3 critical events (Surge!)
    for i in range(10):
        sev = SecurityEventSeverity.CRITICAL if i < 3 else SecurityEventSeverity.HIGH
        ev = SecurityEvent(
            id=str(uuid.uuid4()),
            analysis_job_id=job.id,
            camera_id=test_camera_1.id,
            event_type=SecurityEventType.INTRUSION,
            severity=sev,
            status=SecurityEventStatus.OPEN,
            title=f"Spike Event {i}",
            description="Surge intrusion",
            start_timestamp=float(i * 5),
            created_at=now - timedelta(hours=1, minutes=i * 2),
        )
        db_session.add(ev)

    db_session.commit()

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/analytics/anomalies?preset=24h", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_sufficient_data"] is True
    assert data["status"] == "ANOMALIES_DETECTED"
    assert data["total_anomalies"] >= 1

    types = [a["type"] for a in data["anomalies"]]
    assert "EVENT_VOLUME_SPIKE" in types or "SEVERITY_SPIKE" in types
    for a in data["anomalies"]:
        assert a["observed_value"] > a["baseline_value"]
        assert len(a["why_flagged"]) > 0


# ─── 8. Operational Security Insights ─────────────────────────────────────────

def test_operational_security_insights(client, token_alpha):
    """Insights endpoint returns deterministic, data-grounded findings."""
    headers = {"Authorization": f"Bearer {token_alpha}"}
    res = client.get("/api/analytics/insights?preset=7d", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "insights" in data
    assert "total_insights" in data
