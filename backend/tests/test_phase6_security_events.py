import math
import os
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app, sync_database_schema
from app.models.user import User, UserRole
from app.models.camera import Camera, CameraSourceType, CameraStatus
from app.models.security_zone import SecurityZone, ZoneType
from app.models.security_rule import SecurityRule, SecurityEventSeverity, SecurityEventType
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.detection import Detection
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.core.security import create_access_token, hash_password
from app.vision.events.engine import EventEngine
from app.vision.events.rules import RuleDefinition
from app.vision.events.intrusion import RestrictedZoneDetector
from app.vision.events.loitering import LoiteringDetector
from app.vision.events.stationary import StationaryObjectDetector
from app.vision.events.crowd import CrowdDetector
from app.vision.events.movement import UnusualMovementDetector
from app.services import security_event_service


@pytest.fixture(scope="module")
def db_session():
    sync_database_schema()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def operator_a(db_session):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"operator_a_{uid[:8]}@sentinel.ai",
        name="SOC Lead Alpha",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def operator_b(db_session):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"operator_b_{uid[:8]}@sentinel.ai",
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
def shared_camera(db_session):
    cam = Camera(
        id=str(uuid.uuid4()),
        name="Main Perimeter Cam 01",
        location="North Perimeter Gate",
        stream_url="rtsp://streams.sentinel.internal/cam01",
        source_type=CameraSourceType.RTSP,
        status=CameraStatus.ONLINE,
        is_enabled=True,
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)
    return cam


# ════════════════════════════════════════════════════════════════════════════════
# 1. AUTHENTICATION & AUTHORIZATION TESTS
# ════════════════════════════════════════════════════════════════════════════════

def test_unauthenticated_requests_rejected(client):
    """Verify unauthenticated requests return 401 Unauthorized across Phase 6 endpoints."""
    res_zones = client.get("/api/security-zones")
    assert res_zones.status_code == 401

    res_rules = client.get("/api/security-rules")
    assert res_rules.status_code == 401

    res_events = client.get("/api/security-events")
    assert res_events.status_code == 401

    res_metrics = client.get("/api/security-events/metrics")
    assert res_metrics.status_code == 401


def test_invalid_jwt_rejected(client):
    """Verify invalid or malformed Bearer tokens return 401 Unauthorized."""
    bad_headers = {"Authorization": "Bearer invalid.token.signature"}
    assert client.get("/api/security-zones", headers=bad_headers).status_code == 401
    assert client.get("/api/security-rules", headers=bad_headers).status_code == 401
    assert client.get("/api/security-events", headers=bad_headers).status_code == 401


def test_user_resource_ownership_isolation(client, auth_headers_a, auth_headers_b, shared_camera):
    """Verify strict tenant isolation: Operator B cannot access or modify Operator A's zones/rules/events."""
    # Operator A creates a zone
    zone_payload = {
        "camera_id": shared_camera.id,
        "name": "Operator A Restricted Zone",
        "zone_type": "RESTRICTED",
        "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.4, "y": 0.1}, {"x": 0.4, "y": 0.4}, {"x": 0.1, "y": 0.4}],
        "is_enabled": True,
    }
    create_zone_res = client.post("/api/security-zones", json=zone_payload, headers=auth_headers_a)
    assert create_zone_res.status_code == 201
    zone_a_id = create_zone_res.json()["id"]

    # Operator B attempts to get Operator A's zone
    assert client.get(f"/api/security-zones/{zone_a_id}", headers=auth_headers_b).status_code == 404

    # Operator B attempts to delete Operator A's zone
    assert client.delete(f"/api/security-zones/{zone_a_id}", headers=auth_headers_b).status_code == 404

    # Operator A creates a rule in zone A
    rule_payload = {
        "camera_id": shared_camera.id,
        "zone_id": zone_a_id,
        "name": "Operator A Intrusion Rule",
        "event_type": "INTRUSION",
        "severity": "HIGH",
        "minimum_confidence": 0.7,
        "class_filters": ["person"],
        "is_enabled": True,
    }
    create_rule_res = client.post("/api/security-rules", json=rule_payload, headers=auth_headers_a)
    assert create_rule_res.status_code == 201
    rule_a_id = create_rule_res.json()["id"]

    # Operator B cannot view or toggle Operator A's rule
    assert client.get(f"/api/security-rules/{rule_a_id}", headers=auth_headers_b).status_code == 404
    assert client.patch(f"/api/security-rules/{rule_a_id}/status?is_enabled=false", headers=auth_headers_b).status_code == 404
    assert client.delete(f"/api/security-rules/{rule_a_id}", headers=auth_headers_b).status_code == 404


# ════════════════════════════════════════════════════════════════════════════════
# 2. ERROR HANDLING TESTS (400, 404, 422)
# ════════════════════════════════════════════════════════════════════════════════

def test_security_zone_validation_errors(client, auth_headers_a, shared_camera):
    """Test validation errors for invalid polygon coordinates."""
    # Polygon with fewer than 3 vertices
    bad_poly = {
        "camera_id": shared_camera.id,
        "name": "Degenerate Zone",
        "zone_type": "RESTRICTED",
        "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.2}],
        "is_enabled": True,
    }
    res = client.post("/api/security-zones", json=bad_poly, headers=auth_headers_a)
    assert res.status_code in [400, 422]

    # Polygon with coordinates outside [0.0, 1.0]
    out_of_bounds = {
        "camera_id": shared_camera.id,
        "name": "Out of Bounds Zone",
        "zone_type": "RESTRICTED",
        "coordinates": [{"x": -0.5, "y": 0.1}, {"x": 1.5, "y": 0.1}, {"x": 0.5, "y": 1.2}],
        "is_enabled": True,
    }
    res2 = client.post("/api/security-zones", json=out_of_bounds, headers=auth_headers_a)
    assert res2.status_code in [400, 422]


def test_security_rule_validation_errors(client, auth_headers_a, shared_camera):
    """Test validation errors for invalid rule parameters."""
    # Non-existent zone reference
    bad_zone_rule = {
        "camera_id": shared_camera.id,
        "zone_id": str(uuid.uuid4()),
        "name": "Orphan Rule",
        "event_type": "INTRUSION",
        "severity": "CRITICAL",
        "is_enabled": True,
    }
    res = client.post("/api/security-rules", json=bad_zone_rule, headers=auth_headers_a)
    assert res.status_code in [400, 404, 422]


def test_nonexistent_event_returns_404(client, auth_headers_a):
    """Test that requesting a non-existent event ID returns 404 Not Found."""
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/security-events/{fake_id}", headers=auth_headers_a)
    assert res.status_code == 404


def test_invalid_event_status_transition_returns_400(client, auth_headers_a, db_session, operator_a, shared_camera):
    """Test that updating an event to an invalid status string returns 400 Bad Request."""
    # Create dummy job and event
    job = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=operator_a.id,
        camera_id=shared_camera.id,
        source_type="UPLOAD",
        source_path="./dummy.mp4",
        original_filename="dummy.mp4",
        status=JobStatus.COMPLETED,
    )
    event = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job.id,
        camera_id=shared_camera.id,
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.HIGH,
        status=SecurityEventStatus.OPEN,
        title="Test Event",
        description="Test",
        start_timestamp=0.0,
    )
    db_session.add_all([job, event])
    db_session.commit()

    res = client.patch(
        f"/api/security-events/{event.id}/status",
        json={"status": "INVALID_STATUS_XYZ"},
        headers=auth_headers_a,
    )
    assert res.status_code in [400, 422]


# ════════════════════════════════════════════════════════════════════════════════
# 3. RULE ENGINE UNIT & DETECTOR TESTING (ALL 5 RULE TYPES)
# ════════════════════════════════════════════════════════════════════════════════

def test_rule_1_intrusion_detector_boundary_crossing():
    """Verify Rule 1 (INTRUSION): fires when tracked object crosses boundary outside -> inside."""
    rule = RuleDefinition(
        id="rule-intrusion-1",
        name="Perimeter Intrusion",
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.CRITICAL,
        minimum_confidence=0.5,
        class_filters=["person"],
        zone_id="zone-1",
        zone_name="Restricted Vault",
        # Zone is normalized square [0.2, 0.2] to [0.8, 0.8]
        zone_coordinates=[{"x": 0.2, "y": 0.2}, {"x": 0.8, "y": 0.2}, {"x": 0.8, "y": 0.8}, {"x": 0.2, "y": 0.8}],
    )
    detector = RestrictedZoneDetector([rule])

    # Frame 0: Track 10 is at (50, 50) -> normalized (0.078, 0.104) in 640x480 -> OUTSIDE
    tracks_f0 = [{"track_id": 10, "class_name": "person", "confidence": 0.95, "center_x": 50, "center_y": 50}]
    events_f0 = detector.evaluate(
        frame_index=0, timestamp_seconds=0.0, result_id="r0",
        tracks=tracks_f0, trajectory_history={10: tracks_f0},
        frame_width=640, frame_height=480,
    )
    assert len(events_f0) == 0, "Should not trigger while outside zone"

    # Frame 1: Track 10 moves to (320, 240) -> normalized (0.5, 0.5) -> INSIDE
    tracks_f1 = [{"track_id": 10, "class_name": "person", "confidence": 0.96, "center_x": 320, "center_y": 240}]
    events_f1 = detector.evaluate(
        frame_index=1, timestamp_seconds=2.0, result_id="r1",
        tracks=tracks_f1, trajectory_history={10: tracks_f0 + tracks_f1},
        frame_width=640, frame_height=480,
    )
    assert len(events_f1) == 1, "Should trigger exactly once upon boundary crossing"
    ev = events_f1[0]
    assert ev.event_type == SecurityEventType.INTRUSION
    assert ev.severity == SecurityEventSeverity.CRITICAL
    assert ev.track_id == 10
    assert ev.class_name == "person"
    assert ev.metadata["zone_id"] == "zone-1"
    assert "entry_point" in ev.metadata

    # Frame 2: Track 10 stays at (320, 240) -> INSIDE (should NOT re-trigger duplicate event)
    tracks_f2 = [{"track_id": 10, "class_name": "person", "confidence": 0.96, "center_x": 320, "center_y": 240}]
    events_f2 = detector.evaluate(
        frame_index=2, timestamp_seconds=4.0, result_id="r2",
        tracks=tracks_f2, trajectory_history={10: tracks_f0 + tracks_f1 + tracks_f2},
        frame_width=640, frame_height=480,
    )
    assert len(events_f2) == 0, "Deduplication: should not re-trigger while remaining inside"


def test_rule_2_loitering_detector_duration_threshold():
    """Verify Rule 2 (LOITERING): triggers when track stays inside zone for >= threshold_seconds."""
    rule = RuleDefinition(
        id="rule-loiter-1",
        name="Lobby Loitering",
        event_type=SecurityEventType.LOITERING,
        severity=SecurityEventSeverity.MEDIUM,
        threshold_seconds=10.0,
        minimum_confidence=0.5,
        class_filters=["person"],
        zone_id="zone-lobby",
        zone_name="Main Lobby",
        zone_coordinates=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0}],
    )
    detector = LoiteringDetector([rule])

    # t = 0s: enters zone
    t0 = [{"track_id": 20, "class_name": "person", "confidence": 0.9, "center_x": 300, "center_y": 200}]
    assert len(detector.evaluate(0, 0.0, "r0", t0, {}, 640, 480)) == 0

    # t = 5s: inside 5s (< 10s threshold)
    t1 = [{"track_id": 20, "class_name": "person", "confidence": 0.9, "center_x": 305, "center_y": 205}]
    assert len(detector.evaluate(1, 5.0, "r1", t1, {}, 640, 480)) == 0

    # t = 10.5s: duration = 10.5s (>= 10.0s threshold) -> TRIGGERS
    t2 = [{"track_id": 20, "class_name": "person", "confidence": 0.9, "center_x": 310, "center_y": 210}]
    events = detector.evaluate(2, 10.5, "r2", t2, {}, 640, 480)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == SecurityEventType.LOITERING
    assert ev.duration_seconds is not None
    assert ev.duration_seconds >= 10.0
    assert ev.metadata["observed_duration_seconds"] >= 10.0
    assert ev.is_active is True

    # t = 15s: continuous loitering updates existing candidate without emitting duplicate new event
    t3 = [{"track_id": 20, "class_name": "person", "confidence": 0.9, "center_x": 310, "center_y": 210}]
    events_cont = detector.evaluate(3, 15.0, "r3", t3, {}, 640, 480)
    assert len(events_cont) == 0  # does not add new candidate to candidates list
    assert ev.duration_seconds == 15.0  # ongoing candidate duration is updated in place


def test_rule_3_stationary_object_detector():
    """Verify Rule 3 (STATIONARY_OBJECT): triggers when displacement <= move_thresh over duration >= dur_thresh."""
    rule = RuleDefinition(
        id="rule-stat-1",
        name="Unattended Bag Detection",
        event_type=SecurityEventType.STATIONARY_OBJECT,
        severity=SecurityEventSeverity.HIGH,
        threshold_value=20.0,     # max 20px displacement
        threshold_seconds=15.0,   # min 15s duration
        minimum_confidence=0.5,
        class_filters=["suitcase", "backpack"],
    )
    detector = StationaryObjectDetector([rule])

    # Trajectory history spanning 16 seconds with only 5 pixels total displacement
    history = [
        {"timestamp_seconds": 0.0, "center_x": 200.0, "center_y": 150.0, "confidence": 0.9},
        {"timestamp_seconds": 8.0, "center_x": 202.0, "center_y": 151.0, "confidence": 0.9},
        {"timestamp_seconds": 16.0, "center_x": 203.0, "center_y": 152.0, "confidence": 0.9},
    ]
    tracks = [{"track_id": 30, "class_name": "backpack", "confidence": 0.9, "center_x": 203.0, "center_y": 152.0}]

    events = detector.evaluate(
        frame_index=8, timestamp_seconds=16.0, result_id="r8",
        tracks=tracks, trajectory_history={30: history},
        frame_width=640, frame_height=480,
    )
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == SecurityEventType.STATIONARY_OBJECT
    assert ev.severity == SecurityEventSeverity.HIGH
    assert ev.metadata["observed_displacement_pixels"] <= 20.0
    assert ev.duration_seconds is not None
    assert ev.duration_seconds >= 15.0


def test_rule_4_crowd_density_detector():
    """Verify Rule 4 (CROWD_DENSITY): triggers when object count in zone >= crowd_threshold."""
    rule = RuleDefinition(
        id="rule-crowd-1",
        name="Exit Hallway Crowd Alert",
        event_type=SecurityEventType.CROWD_DENSITY,
        severity=SecurityEventSeverity.HIGH,
        threshold_value=4.0,  # 4 or more persons
        minimum_confidence=0.5,
        class_filters=["person"],
        zone_id="zone-hallway",
        zone_name="Exit Hallway",
        zone_coordinates=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0}],
    )
    detector = CrowdDetector([rule])

    # 3 persons inside -> threshold 4 not met
    tracks_3 = [
        {"track_id": i, "class_name": "person", "confidence": 0.9, "center_x": 100 * i, "center_y": 100}
        for i in range(1, 4)
    ]
    assert len(detector.evaluate(0, 0.0, "r0", tracks_3, {}, 640, 480)) == 0

    # 5 persons inside -> threshold 4 met -> TRIGGERS
    tracks_5 = [
        {"track_id": i, "class_name": "person", "confidence": 0.9, "center_x": 100 * i, "center_y": 100}
        for i in range(1, 6)
    ]
    events = detector.evaluate(1, 2.0, "r1", tracks_5, {}, 640, 480)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == SecurityEventType.CROWD_DENSITY
    assert ev.metadata["threshold"] == 4
    assert ev.metadata["peak_count"] == 5


def test_rule_5_unusual_movement_speed_detector():
    """Verify Rule 5 (UNUSUAL_MOVEMENT): triggers when track speed >= speed_threshold."""
    rule = RuleDefinition(
        id="rule-speed-1",
        name="Running Person Alert",
        event_type=SecurityEventType.UNUSUAL_MOVEMENT,
        severity=SecurityEventSeverity.HIGH,
        threshold_value=200.0,  # 200 pixels/second
        minimum_confidence=0.5,
        class_filters=["person"],
    )
    detector = UnusualMovementDetector([rule])

    # Track travels 300 pixels in 0.5s -> speed = 600 px/s (exceeds 200 px/s threshold)
    history = [
        {"timestamp_seconds": 1.0, "center_x": 100.0, "center_y": 100.0, "confidence": 0.95},
        {"timestamp_seconds": 1.5, "center_x": 400.0, "center_y": 100.0, "confidence": 0.95},
    ]
    tracks = [{"track_id": 50, "class_name": "person", "confidence": 0.95, "center_x": 400.0, "center_y": 100.0}]

    events = detector.evaluate(
        frame_index=1, timestamp_seconds=1.5, result_id="r1",
        tracks=tracks, trajectory_history={50: history},
        frame_width=640, frame_height=480,
    )
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == SecurityEventType.UNUSUAL_MOVEMENT
    assert ev.metadata["observed_speed_px_s"] >= 200.0


# ════════════════════════════════════════════════════════════════════════════════
# 4. DUPLICATE EVENT & DEDUPLICATION TESTING
# ════════════════════════════════════════════════════════════════════════════════

def test_deduplication_and_cooldown_cohesion():
    """
    Verify EventEngine processes 10 consecutive frames with the same track inside zone
    without generating 10 separate duplicate events.
    """
    rule = RuleDefinition(
        id="rule-intrusion-dedup",
        name="Intrusion Dedup Test",
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.HIGH,
        minimum_confidence=0.5,
        class_filters=["person"],
        zone_id="z-dedup",
        zone_name="Secure Area",
        zone_coordinates=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0}],
    )
    engine = EventEngine([rule])

    # 10 consecutive frames:
    # Frame 0: object starts outside
    # Frames 1-9: object is inside
    history = []
    total_emitted = 0

    # Outside
    t0 = [{"track_id": 99, "class_name": "person", "confidence": 0.9, "center_x": -50, "center_y": -50}]
    history.append(t0[0])
    cands0 = engine.process_frame(0, 0.0, "f0", t0, {99: history}, 640, 480)
    total_emitted += len(cands0)

    # 9 frames inside
    for f in range(1, 10):
        ts = f * 1.0
        t_in = [{"track_id": 99, "class_name": "person", "confidence": 0.9, "center_x": 320, "center_y": 240}]
        history.append(t_in[0])
        cands = engine.process_frame(f, ts, f"f{f}", t_in, {99: history}, 640, 480)
        total_emitted += len(cands)

    final_events = engine.finalize(10.0)
    # Exactly 1 event should have been emitted upon crossing and retained in finalized list
    assert total_emitted == 1, f"Expected 1 emitted event on boundary crossing, got {total_emitted}"
    assert len(final_events) == 1, f"Expected 1 finalized event, got {len(final_events)}"


# ════════════════════════════════════════════════════════════════════════════════
# 5. END-TO-END DATABASE PERSISTENCE & API RETRIEVAL
# ════════════════════════════════════════════════════════════════════════════════

def test_security_event_lifecycle_and_metrics(client, auth_headers_a, db_session, operator_a, shared_camera):
    """
    Test full lifecycle of security events in database:
    Create job -> Add events -> Query events -> Update status -> Verify metrics.
    """
    # 1. Create analysis job
    job = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=operator_a.id,
        camera_id=shared_camera.id,
        source_type="UPLOAD",
        source_path="./e2e.mp4",
        original_filename="e2e.mp4",
        status=JobStatus.COMPLETED,
    )
    # 2. Create 2 security events
    evt_intrusion = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job.id,
        camera_id=shared_camera.id,
        track_id=7,
        class_name="person",
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.CRITICAL,
        status=SecurityEventStatus.OPEN,
        title="North Gate Intrusion Event",
        description="Breach of perimeter fence.",
        start_timestamp=12.4,
        confidence=0.97,
        metadata_json={"zone_name": "Perimeter Gate"},
    )
    evt_loitering = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job.id,
        camera_id=shared_camera.id,
        track_id=8,
        class_name="person",
        event_type=SecurityEventType.LOITERING,
        severity=SecurityEventSeverity.MEDIUM,
        status=SecurityEventStatus.OPEN,
        title="North Gate Loitering Event",
        description="Person loitering near gate.",
        start_timestamp=25.0,
        confidence=0.89,
        metadata_json={"zone_name": "Perimeter Gate"},
    )
    db_session.add_all([job, evt_intrusion, evt_loitering])
    db_session.commit()

    # 3. GET /api/security-events with filtering
    res_list = client.get("/api/security-events?event_type=INTRUSION", headers=auth_headers_a)
    assert res_list.status_code == 200
    intrusions = res_list.json()
    assert any(e["id"] == evt_intrusion.id for e in intrusions)

    # 4. GET /api/security-events/{id}
    res_single = client.get(f"/api/security-events/{evt_intrusion.id}", headers=auth_headers_a)
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["id"] == evt_intrusion.id
    assert single_data["event_type"] == "INTRUSION"
    assert single_data["severity"] == "CRITICAL"
    assert single_data["status"] == "OPEN"
    assert single_data["camera_name"] == shared_camera.name
    assert single_data["metadata_json"]["zone_name"] == "Perimeter Gate"

    # 5. PATCH /api/security-events/{id}/status -> ACKNOWLEDGED -> RESOLVED
    ack_res = client.patch(
        f"/api/security-events/{evt_intrusion.id}/status",
        json={"status": "ACKNOWLEDGED"},
        headers=auth_headers_a,
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    res_res = client.patch(
        f"/api/security-events/{evt_intrusion.id}/status",
        json={"status": "RESOLVED"},
        headers=auth_headers_a,
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"

    # 6. GET /api/security-events/metrics
    metrics_res = client.get("/api/security-events/metrics", headers=auth_headers_a)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_events"] >= 2
    assert "open_events" in metrics
    assert "high_severity_events" in metrics
    assert "by_type" in metrics
