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
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.models.incident_report import IncidentReport, IncidentReportStatus
from app.core.security import create_access_token, hash_password


@pytest.fixture(scope="module")
def db_session():
    sync_database_schema()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def user_alpha(db_session):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"alpha_inc_{uid[:8]}@sentinel.ai",
        name="Alpha Operator",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def user_beta(db_session):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"beta_inc_{uid[:8]}@sentinel.ai",
        name="Beta Operator",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def auth_alpha(user_alpha):
    token = create_access_token(user_alpha.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def auth_beta(user_beta):
    token = create_access_token(user_beta.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def sample_incident_data(db_session, user_alpha):
    cam = Camera(
        id=str(uuid.uuid4()),
        name="Incident Test Camera",
        location="Zone 1",
        stream_url="rtsp://internal/cam1",
        source_type=CameraSourceType.RTSP,
        status=CameraStatus.ONLINE,
        is_enabled=True,
    )
    db_session.add(cam)
    db_session.commit()

    zone = SecurityZone(
        id=str(uuid.uuid4()),
        user_id=user_alpha.id,
        camera_id=cam.id,
        name="Restricted Zone Alpha",
        zone_type=ZoneType.RESTRICTED,
        coordinates=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}],
        is_enabled=True,
    )
    db_session.add(zone)
    db_session.commit()

    rule = SecurityRule(
        id=str(uuid.uuid4()),
        user_id=user_alpha.id,
        camera_id=cam.id,
        zone_id=zone.id,
        name="Zone Intrusion Rule",
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.HIGH,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()

    job = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=user_alpha.id,
        camera_id=cam.id,
        source_type="UPLOAD",
        source_path="./storage/uploads/test.mp4",
        original_filename="incident_test.mp4",
        status=JobStatus.COMPLETED,
        progress=100,
        duration_seconds=60.0,
    )
    db_session.add(job)
    db_session.commit()

    evt1 = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job.id,
        camera_id=cam.id,
        rule_id=rule.id,
        track_id=1,
        class_name="person",
        event_type=SecurityEventType.INTRUSION,
        severity=SecurityEventSeverity.HIGH,
        status=SecurityEventStatus.OPEN,
        title="Unauthorized Zone Breach",
        description="Person detected inside Restricted Zone Alpha.",
        start_timestamp=10.0,
        end_timestamp=15.0,
        duration_seconds=5.0,
        confidence=0.92,
    )
    evt2 = SecurityEvent(
        id=str(uuid.uuid4()),
        analysis_job_id=job.id,
        camera_id=cam.id,
        rule_id=rule.id,
        track_id=1,
        class_name="person",
        event_type=SecurityEventType.LOITERING,
        severity=SecurityEventSeverity.MEDIUM,
        status=SecurityEventStatus.OPEN,
        title="Subject Loitering",
        description="Person loitering in vicinity for 20 seconds.",
        start_timestamp=20.0,
        end_timestamp=40.0,
        duration_seconds=20.0,
        confidence=0.88,
    )
    db_session.add_all([evt1, evt2])
    db_session.commit()

    return {
        "user_id": user_alpha.id,
        "job_id": job.id,
        "event_ids": [evt1.id, evt2.id],
    }


def test_create_incident_report_validation(client, auth_alpha):
    """Test validation: at least one event ID is required."""
    res = client.post("/api/incidents", json={"event_ids": []}, headers=auth_alpha)
    assert res.status_code in [400, 422]


def test_create_and_generate_incident_report(client, auth_alpha, sample_incident_data):
    """Test creating an incident report and executing AI analysis."""
    payload = {
        "event_ids": sample_incident_data["event_ids"],
        "analysis_job_id": sample_incident_data["job_id"],
    }
    res = client.post("/api/incidents", json=payload, headers=auth_alpha)
    assert res.status_code == 202
    data = res.json()
    assert data["status"] in ["GENERATING", "COMPLETED"]
    report_id = data["id"]

    # Retrieve report
    get_res = client.get(f"/api/incidents/{report_id}", headers=auth_alpha)
    assert get_res.status_code == 200
    report = get_res.json()
    assert report["id"] == report_id
    assert report["status"] == "COMPLETED"
    assert report["summary"] is not None
    assert len(report["summary"]) > 0
    assert report["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert isinstance(report["timeline"], list)
    assert isinstance(report["recommendations"], list)
    assert report["disclaimer"] is not None


def test_incident_ownership_isolation(client, auth_alpha, auth_beta, sample_incident_data):
    """Test user isolation: user_beta cannot access or delete user_alpha's incident report."""
    payload = {
        "event_ids": sample_incident_data["event_ids"],
        "analysis_job_id": sample_incident_data["job_id"],
    }
    create_res = client.post("/api/incidents", json=payload, headers=auth_alpha)
    report_id = create_res.json()["id"]

    # Beta attempts to read Alpha's report
    get_res = client.get(f"/api/incidents/{report_id}", headers=auth_beta)
    assert get_res.status_code == 404

    # Beta attempts to delete Alpha's report
    del_res = client.delete(f"/api/incidents/{report_id}", headers=auth_beta)
    assert del_res.status_code == 404

    # Alpha successfully deletes own report
    alpha_del = client.delete(f"/api/incidents/{report_id}", headers=auth_alpha)
    assert alpha_del.status_code == 204
