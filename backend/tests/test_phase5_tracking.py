import os
import uuid
import numpy as np
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal
from app.main import app, sync_database_schema
from app.models.user import User, UserRole
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.detection import Detection
from app.models.tracked_object import TrackedObject
from app.models.track_point import TrackPoint
from app.core.security import create_access_token, hash_password
from app.vision.detection.detector import BoundingBox, DetectionResult
from app.vision.tracking.tracker import TrackedDetection
from app.vision.tracking.track_manager import get_track_manager
from app.vision.tracking.trajectory import (
    calculate_center,
    calculate_displacement,
    calculate_trajectory_distance,
)
from app.vision.detection.annotation import annotate_frame
from app.services import tracking_service


@pytest.fixture(scope="module")
def db_session():
    sync_database_schema()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_user(db_session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"tracker_{user_id[:8]}@sentinel.ai",
        name="Tracking Operator",
        password_hash=hash_password("Password123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def auth_headers(test_user):
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ─── Unit Tests: Trajectory Math Utilities ───────────────────────────────────

def test_calculate_center():
    """Verify center coordinate computation from bounding box edges."""
    cx, cy = calculate_center(100, 100, 200, 300)
    assert cx == 150.0
    assert cy == 200.0


def test_calculate_displacement():
    """Verify Euclidean net displacement calculation between start and end points."""
    disp = calculate_displacement((0.0, 0.0), (3.0, 4.0))
    assert abs(disp - 5.0) < 1e-5


def test_calculate_trajectory_distance():
    """Verify cumulative trajectory path length across points."""
    points = [(0.0, 0.0), (3.0, 0.0), (3.0, 4.0)]
    dist = calculate_trajectory_distance(points)
    assert abs(dist - 7.0) < 1e-5

    # Test single point and empty edge cases
    assert calculate_trajectory_distance([(10.0, 10.0)]) == 0.0
    assert calculate_trajectory_distance([]) == 0.0


# ─── Unit Tests: TrackManager Isolation & Session Management ─────────────────

def test_track_manager_session_isolation():
    """Verify TrackManager isolates tracker sessions per analysis job."""
    mgr = get_track_manager()
    job_id_1 = str(uuid.uuid4())
    job_id_2 = str(uuid.uuid4())

    t1 = mgr.create_tracker(job_id_1)
    t2 = mgr.create_tracker(job_id_2)

    assert t1 is not None
    assert t2 is not None
    assert t1 is not t2
    assert mgr.has_tracker(job_id_1)
    assert mgr.has_tracker(job_id_2)

    # Closing t1 does not affect t2
    mgr.close_tracker(job_id_1)
    assert not mgr.has_tracker(job_id_1)
    assert mgr.has_tracker(job_id_2)

    mgr.close_tracker(job_id_2)
    assert not mgr.has_tracker(job_id_2)


# ─── Unit Tests: Trajectory Rendering on Annotated Frames ────────────────────

def test_annotation_with_trajectories_and_track_id():
    """Verify annotate_frame renders track ID badges and trajectory trails."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = [
        DetectionResult(
            class_id=0,
            class_name="person",
            confidence=0.92,
            bbox=BoundingBox(x1=50, y1=50, x2=150, y2=200, width=100, height=150),
            track_id=1,
        )
    ]
    trajectories = {
        1: [(60.0, 80.0), (80.0, 100.0), (100.0, 125.0)]
    }

    annotated = annotate_frame(
        frame=frame,
        detections=detections,
        trajectories=trajectories,
    )
    assert annotated.shape == frame.shape
    # Frame pixels should be modified by drawing the bbox, text badge, and trajectory line
    assert not np.array_equal(frame, annotated)


# ─── Integration Tests: Tracking Service & Database Persistence ──────────────

def test_tracking_service_persistence_and_summary(db_session, test_user):
    """Verify database persistence of TrackedObject, TrackPoint, and summary aggregation."""
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=job_id,
        user_id=test_user.id,
        source_type="surveillance_feed",
        original_filename="tracking_test.mp4",
        source_path="/tmp/fake_tracking_test.mp4",
        status=JobStatus.COMPLETED,
        progress=100,
        sampled_frames=3,
        processed_frames=3,
    )
    db_session.add(job)
    db_session.commit()

    # Create 3 frames with detections
    r1 = AnalysisResult(
        id=str(uuid.uuid4()),
        analysis_job_id=job_id,
        frame_index=0,
        timestamp_seconds=0.0,
        frame_path="/tmp/f0.jpg",
        detection_count=1,
        width=1280,
        height=720,
    )
    r2 = AnalysisResult(
        id=str(uuid.uuid4()),
        analysis_job_id=job_id,
        frame_index=30,
        timestamp_seconds=1.0,
        frame_path="/tmp/f1.jpg",
        detection_count=1,
        width=1280,
        height=720,
    )
    r3 = AnalysisResult(
        id=str(uuid.uuid4()),
        analysis_job_id=job_id,
        frame_index=60,
        timestamp_seconds=2.0,
        frame_path="/tmp/f2.jpg",
        detection_count=1,
        width=1280,
        height=720,
    )
    db_session.add_all([r1, r2, r3])
    db_session.commit()

    # Tracked Object #1: person seen across 3 frames
    track_obj_id = str(uuid.uuid4())
    tracked_obj = TrackedObject(
        id=track_obj_id,
        analysis_job_id=job_id,
        track_id=1,
        class_id=0,
        class_name="person",
        first_seen_timestamp=0.0,
        last_seen_timestamp=2.0,
        first_seen_frame=0,
        last_seen_frame=60,
        total_frames=3,
        average_confidence=0.88,
        max_confidence=0.92,
    )
    db_session.add(tracked_obj)
    db_session.commit()

    # Add 3 track points
    tp1 = TrackPoint(
        id=str(uuid.uuid4()),
        tracked_object_id=track_obj_id,
        analysis_result_id=r1.id,
        frame_index=0,
        timestamp_seconds=0.0,
        x1=100, y1=100, x2=200, y2=300,
        center_x=150.0, center_y=200.0,
        width=100, height=200, confidence=0.85,
    )
    tp2 = TrackPoint(
        id=str(uuid.uuid4()),
        tracked_object_id=track_obj_id,
        analysis_result_id=r2.id,
        frame_index=30,
        timestamp_seconds=1.0,
        x1=150, y1=100, x2=250, y2=300,
        center_x=200.0, center_y=200.0,
        width=100, height=200, confidence=0.88,
    )
    tp3 = TrackPoint(
        id=str(uuid.uuid4()),
        tracked_object_id=track_obj_id,
        analysis_result_id=r3.id,
        frame_index=60,
        timestamp_seconds=2.0,
        x1=200, y1=100, x2=300, y2=300,
        center_x=250.0, center_y=200.0,
        width=100, height=200, confidence=0.92,
    )
    db_session.add_all([tp1, tp2, tp3])
    db_session.commit()

    # Test summary service
    summary = tracking_service.get_tracking_summary(db_session, job_id, test_user.id)
    assert summary["total_tracked_objects"] == 1
    assert summary["tracked_persons"] == 1
    assert summary["tracked_vehicles"] == 0
    assert summary["longest_track_duration_seconds"] == 2.0
    assert summary["most_frequently_tracked_class"] == "person"

    # Test tracked objects list service
    tracks = tracking_service.get_tracked_objects(db_session, job_id, test_user.id)
    assert len(tracks) == 1
    assert tracks[0].track_id == 1
    assert tracks[0].total_frames == 3

    # Test track detail service with trajectory & displacement metrics
    detail = tracking_service.get_track_detail(db_session, job_id, 1, test_user.id)
    assert detail["track_id"] == 1
    assert detail["duration_seconds"] == 2.0
    assert detail["displacement_pixels"] == 100.0  # (250, 200) - (150, 200) = 100
    assert detail["trajectory_distance_pixels"] == 100.0
    assert len(detail["trajectory"]) == 3


# ─── API Endpoint Tests ──────────────────────────────────────────────────────

def test_api_tracking_endpoints(client, db_session, test_user, auth_headers):
    """Verify tracking API endpoints (/tracking/summary, /tracks, /tracks/{track_id})."""
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=job_id,
        user_id=test_user.id,
        source_type="surveillance_feed",
        original_filename="api_tracking_test.mp4",
        source_path="/tmp/fake_api_test.mp4",
        status=JobStatus.COMPLETED,
        progress=100,
    )
    db_session.add(job)
    db_session.commit()

    t_obj = TrackedObject(
        id=str(uuid.uuid4()),
        analysis_job_id=job_id,
        track_id=42,
        class_id=2,
        class_name="car",
        first_seen_timestamp=1.5,
        last_seen_timestamp=5.5,
        first_seen_frame=45,
        last_seen_frame=165,
        total_frames=5,
        average_confidence=0.91,
        max_confidence=0.96,
    )
    db_session.add(t_obj)
    db_session.commit()

    # 1. Summary Endpoint
    resp_sum = client.get(f"/api/video-analysis/{job_id}/tracking/summary", headers=auth_headers)
    assert resp_sum.status_code == 200
    data_sum = resp_sum.json()
    assert data_sum["total_tracked_objects"] == 1
    assert data_sum["tracked_vehicles"] == 1
    assert data_sum["tracked_persons"] == 0
    assert data_sum["most_frequently_tracked_class"] == "car"

    # 2. Track List Endpoint
    resp_tracks = client.get(f"/api/video-analysis/{job_id}/tracks", headers=auth_headers)
    assert resp_tracks.status_code == 200
    data_tracks = resp_tracks.json()
    assert len(data_tracks) == 1
    assert data_tracks[0]["track_id"] == 42
    assert data_tracks[0]["class_name"] == "car"
    assert data_tracks[0]["duration_seconds"] == 4.0

    # 3. Track Detail Endpoint
    resp_detail = client.get(f"/api/video-analysis/{job_id}/tracks/42", headers=auth_headers)
    assert resp_detail.status_code == 200
    data_detail = resp_detail.json()
    assert data_detail["track_id"] == 42
    assert data_detail["duration_seconds"] == 4.0
    assert "displacement_pixels" in data_detail
    assert "trajectory" in data_detail


def test_api_tracking_ownership_protection(client, db_session, test_user, auth_headers):
    """Verify tracking endpoints strictly deny unauthorized user access."""
    # Create another user's job
    other_user_id = str(uuid.uuid4())
    other_user = User(
        id=other_user_id,
        email=f"unauthorized_{other_user_id[:8]}@sentinel.ai",
        name="Unauthorized User",
        password_hash=hash_password("Pass123!"),
        role=UserRole.VIEWER,
    )
    db_session.add(other_user)
    db_session.commit()

    other_job = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=other_user.id,
        source_type="surveillance_feed",
        original_filename="private.mp4",
        source_path="/tmp/private.mp4",
        status=JobStatus.COMPLETED,
    )
    db_session.add(other_job)
    db_session.commit()

    # Try accessing other user's job with test_user token -> 404 (non-leaking)
    resp = client.get(f"/api/video-analysis/{other_job.id}/tracking/summary", headers=auth_headers)
    assert resp.status_code == 404

    resp2 = client.get(f"/api/video-analysis/{other_job.id}/tracks", headers=auth_headers)
    assert resp2.status_code == 404
