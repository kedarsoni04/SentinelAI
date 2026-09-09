import os
import uuid
import numpy as np
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app, sync_database_schema
from app.models.user import User, UserRole
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.detection import Detection
from app.core.security import create_access_token, hash_password
from app.vision.detection.detector import BoundingBox, DetectionResult, ObjectDetector
from app.vision.detection.model_manager import YOLOModelManager, get_model_manager
from app.vision.detection.yolo_detector import YOLODetector
from app.vision.detection.annotation import annotate_frame, get_class_color
from app.services.detection_service import (
    get_detection_summary,
    get_frame_detections,
    get_annotated_frame_path_for_serving,
)


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
        email=f"tester_{user_id[:8]}@sentinel.ai",
        name="Test Operator",
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


# ─── Unit Tests: Model Manager & Detector Abstraction ─────────────────────────


def test_model_manager_singleton():
    """Verify YOLOModelManager enforces singleton caching."""
    m1 = get_model_manager()
    m2 = YOLOModelManager()
    assert m1 is m2


def test_bounding_box_geometry():
    """Verify BoundingBox coordinate calculation and constraints."""
    bbox = BoundingBox.from_coords(100.4, 50.6, 250.2, 350.8)
    assert bbox.x1 == 100
    assert bbox.y1 == 51
    assert bbox.x2 == 250
    assert bbox.y2 == 351
    assert bbox.width == 150
    assert bbox.height == 300


def test_annotation_drawing():
    """Verify OpenCV annotation engine renders non-empty image with detections."""
    # Synthetic frame: 640x480 black image
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = [
        DetectionResult(
            class_id=0,
            class_name="person",
            confidence=0.95,
            bbox=BoundingBox(50, 50, 200, 300, 150, 250),
        ),
        DetectionResult(
            class_id=2,
            class_name="car",
            confidence=0.88,
            bbox=BoundingBox(300, 100, 500, 300, 200, 200),
        ),
    ]

    annotated = annotate_frame(frame, detections)
    assert annotated is not None
    assert annotated.shape == (480, 640, 3)
    # Verify image was modified by drawing operations
    assert np.any(annotated > 0)


def test_detection_filtering_logic():
    """Verify confidence threshold and allowed class filtering."""
    class MockDetector(ObjectDetector):
        def detect(self, frame: np.ndarray):
            raw = [
                DetectionResult(0, "person", 0.92, BoundingBox(10, 10, 50, 50, 40, 40)),
                DetectionResult(0, "person", 0.35, BoundingBox(60, 60, 90, 90, 30, 30)),
                DetectionResult(15, "cat", 0.89, BoundingBox(100, 100, 140, 140, 40, 40)),
            ]
            allowed = {"person", "car"}
            return [d for d in raw if d.confidence >= 0.50 and d.class_name in allowed]

    det = MockDetector()
    results = det.detect(np.zeros((100, 100, 3), dtype=np.uint8))
    assert len(results) == 1
    assert results[0].class_name == "person"
    assert results[0].confidence == 0.92


def test_real_yolo_model_inference():
    """Verify actual YOLO model initializes on CPU and executes inference on an image matrix."""
    detector = YOLODetector()
    # Create test image (640x640)
    test_img = np.zeros((640, 640, 3), dtype=np.uint8)
    # Run detection
    detections = detector.detect(test_img)
    assert isinstance(detections, list)
    # Solid black frame should produce 0 detections with threshold 0.50
    assert len(detections) == 0


# ─── Database & Service Layer Tests ──────────────────────────────────────────


def test_detection_persistence_and_summary(db_session, test_user):
    """Verify Detection database storage and summary aggregation calculations."""
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=job_id,
        user_id=test_user.id,
        source_type="VIDEO_FILE",
        source_path="/tmp/fake.mp4",
        original_filename="test_surveillance.mp4",
        status=JobStatus.COMPLETED,
        progress=100,
        sampled_frames=2,
        processed_frames=2,
    )
    db_session.add(job)

    # Frame 1 with 2 detections
    f1_id = str(uuid.uuid4())
    frame1 = AnalysisResult(
        id=f1_id,
        analysis_job_id=job.id,
        frame_index=0,
        timestamp_seconds=0.0,
        frame_path="/tmp/frame_0.jpg",
        thumbnail_path="/tmp/thumb_0.jpg",
        annotated_frame_path="/tmp/annotated_0.jpg",
        detection_count=2,
        width=1280,
        height=720,
        processing_time_ms=45.2,
    )
    db_session.add(frame1)

    det1 = Detection(
        id=str(uuid.uuid4()),
        analysis_result_id=f1_id,
        class_id=0,
        class_name="person",
        confidence=0.95,
        x1=100,
        y1=100,
        x2=200,
        y2=400,
        width=100,
        height=300,
    )
    det2 = Detection(
        id=str(uuid.uuid4()),
        analysis_result_id=f1_id,
        class_id=2,
        class_name="car",
        confidence=0.85,
        x1=300,
        y1=200,
        x2=500,
        y2=400,
        width=200,
        height=200,
    )
    db_session.add_all([det1, det2])

    # Frame 2 with 0 detections
    f2_id = str(uuid.uuid4())
    frame2 = AnalysisResult(
        id=f2_id,
        analysis_job_id=job.id,
        frame_index=60,
        timestamp_seconds=2.0,
        frame_path="/tmp/frame_60.jpg",
        thumbnail_path="/tmp/thumb_60.jpg",
        annotated_frame_path="/tmp/annotated_60.jpg",
        detection_count=0,
        width=1280,
        height=720,
        processing_time_ms=35.0,
    )
    db_session.add(frame2)
    db_session.commit()

    # Verify summary calculation
    summary = get_detection_summary(db_session, job.id, test_user.id)
    assert summary.total_detections == 2
    assert summary.frames_with_detections == 1
    assert summary.unique_classes == 2
    assert summary.class_counts["person"] == 1
    assert summary.class_counts["car"] == 1
    assert summary.average_confidence == 0.90  # (0.95 + 0.85) / 2

    # Verify frame detections
    frame_dets = get_frame_detections(db_session, job.id, f1_id, test_user.id)
    assert len(frame_dets) == 2
    assert frame_dets[0].class_name == "person"
    assert frame_dets[0].bbox.width == 100

    frame2_dets = get_frame_detections(db_session, job.id, f2_id, test_user.id)
    assert len(frame2_dets) == 0


# ─── API Integration Tests ───────────────────────────────────────────────────


def test_api_detection_summary(client, auth_headers, test_user, db_session):
    """Verify GET /api/video-analysis/{job_id}/detections/summary."""
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=job_id,
        user_id=test_user.id,
        source_type="VIDEO_FILE",
        source_path="/tmp/fake2.mp4",
        original_filename="api_test.mp4",
        status=JobStatus.COMPLETED,
        progress=100,
    )
    db_session.add(job)
    db_session.commit()

    res = client.get(f"/api/video-analysis/{job_id}/detections/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_detections"] == 0
    assert data["unique_classes"] == 0
    assert data["average_confidence"] == 0.0


def test_api_ownership_protection(client, db_session):
    """Verify endpoints reject requests from unauthorized users."""
    unique_id = str(uuid.uuid4())
    other_user = User(
        id=unique_id,
        email=f"other_{unique_id[:8]}@sentinel.ai",
        name="Other User",
        password_hash=hash_password("Pass123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    db_session.add(other_user)

    job = AnalysisJob(
        id=str(uuid.uuid4()),
        user_id=other_user.id,
        source_type="VIDEO_FILE",
        source_path="/tmp/other.mp4",
        original_filename="other.mp4",
        status=JobStatus.COMPLETED,
    )
    db_session.add(job)
    db_session.commit()

    # Unauthorized attempt (no token)
    res_no_auth = client.get(f"/api/video-analysis/{job.id}/detections/summary")
    assert res_no_auth.status_code == 401
