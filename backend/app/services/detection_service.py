import os
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis_job import AnalysisJob
from app.models.analysis_result import AnalysisResult
from app.models.detection import Detection
from app.schemas.detection import BoundingBox, DetectionResponse, DetectionSummary
from app.services.video_analysis_service import get_job_by_id


def get_detection_summary(db: Session, job_id: str, user_id: str) -> DetectionSummary:
    """
    Calculate high-level object detection statistics for an entire analysis job.
    Enforces user ownership and safely handles empty detections without failing.
    """
    job = get_job_by_id(db, job_id, user_id)

    detections = (
        db.query(Detection)
        .join(AnalysisResult, Detection.analysis_result_id == AnalysisResult.id)
        .filter(AnalysisResult.analysis_job_id == job.id)
        .all()
    )

    if not detections:
        return DetectionSummary(
            total_detections=0,
            frames_with_detections=0,
            unique_classes=0,
            average_confidence=0.0,
            class_counts={},
        )

    class_counts: Dict[str, int] = {}
    total_conf = 0.0

    for d in detections:
        c_name = d.class_name.lower()
        class_counts[c_name] = class_counts.get(c_name, 0) + 1
        total_conf += d.confidence

    total_detections = len(detections)
    unique_frames = len({d.analysis_result_id for d in detections})
    avg_conf = round(total_conf / total_detections, 4)

    return DetectionSummary(
        total_detections=total_detections,
        frames_with_detections=unique_frames,
        unique_classes=len(class_counts),
        average_confidence=avg_conf,
        class_counts=dict(sorted(class_counts.items(), key=lambda item: item[1], reverse=True)),
    )


def get_frame_detections(
    db: Session, job_id: str, result_id: str, user_id: str
) -> List[DetectionResponse]:
    """
    Retrieve all object detections for a specific sampled frame.
    Enforces job ownership and verifies result_id belongs to the specified job.
    """
    job = get_job_by_id(db, job_id, user_id)

    frame_result = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.id == result_id, AnalysisResult.analysis_job_id == job.id)
        .first()
    )
    if not frame_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Frame result '{result_id}' not found for job '{job_id}'.",
        )

    detections = (
        db.query(Detection)
        .filter(Detection.analysis_result_id == frame_result.id)
        .order_by(Detection.confidence.desc())
        .all()
    )

    return [
        DetectionResponse(
            id=d.id,
            class_id=d.class_id,
            class_name=d.class_name,
            confidence=d.confidence,
            bbox=BoundingBox(
                x1=d.x1,
                y1=d.y1,
                x2=d.x2,
                y2=d.y2,
                width=d.width,
                height=d.height,
            ),
            track_id=d.track_id,
        )
        for d in detections
    ]


def get_annotated_frame_path_for_serving(
    db: Session, job_id: str, filename: str, user_id: str
) -> str:
    """
    Resolve and validate an annotated frame file path for HTTP serving.
    Guarantees user ownership and prevents directory traversal attacks.
    """
    # Enforce job ownership first
    job = get_job_by_id(db, job_id, user_id)

    # Filename sanity check
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename specified.",
        )

    if not filename.endswith(".jpg"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format requested.",
        )

    job_annotated_dir = os.path.abspath(os.path.join(settings.annotated_path, job.id))
    target_path = os.path.abspath(os.path.join(job_annotated_dir, filename))

    # Prevent path traversal
    if not target_path.startswith(job_annotated_dir):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to requested file path.",
        )

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotated frame file '{filename}' not found.",
        )

    return target_path
