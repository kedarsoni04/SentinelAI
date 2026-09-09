import logging
import math
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.track_point import TrackPoint
from app.models.tracked_object import TrackedObject
from app.vision.tracking.trajectory import (
    calculate_displacement,
    calculate_trajectory_distance,
)

logger = logging.getLogger("sentinel.services.tracking")

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}


def _assert_job_access(db: Session, job_id: str, user_id: str) -> AnalysisJob:
    """
    Retrieve AnalysisJob by ID and validate user ownership.
    Returns 404 for missing or unauthorized access (non-leaking).
    """
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found.",
        )
    return job


def get_tracking_summary(db: Session, job_id: str, user_id: str) -> dict:
    """
    Aggregate tracking statistics for a completed analysis job.

    Returns:
        Dict containing total tracked objects, class breakdowns,
        duration stats, and most frequent class.
    """
    _assert_job_access(db, job_id, user_id)

    tracks: List[TrackedObject] = (
        db.query(TrackedObject)
        .filter(TrackedObject.analysis_job_id == job_id)
        .all()
    )

    if not tracks:
        return {
            "total_tracked_objects": 0,
            "tracked_persons": 0,
            "tracked_vehicles": 0,
            "longest_track_duration_seconds": 0.0,
            "average_track_duration_seconds": 0.0,
            "average_observations_per_track": 0.0,
            "most_frequently_tracked_class": None,
        }

    durations = []
    class_counts: dict = {}
    total_frames_list = []

    for t in tracks:
        duration = t.last_seen_timestamp - t.first_seen_timestamp
        durations.append(duration)
        total_frames_list.append(t.total_frames)
        class_counts[t.class_name] = class_counts.get(t.class_name, 0) + 1

    tracked_persons = sum(1 for t in tracks if t.class_name == "person")
    tracked_vehicles = sum(1 for t in tracks if t.class_name in VEHICLE_CLASSES)
    longest = round(max(durations), 2) if durations else 0.0
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0
    avg_obs = round(sum(total_frames_list) / len(total_frames_list), 2) if total_frames_list else 0.0
    most_frequent = max(class_counts, key=class_counts.get) if class_counts else None

    return {
        "total_tracked_objects": len(tracks),
        "tracked_persons": tracked_persons,
        "tracked_vehicles": tracked_vehicles,
        "longest_track_duration_seconds": longest,
        "average_track_duration_seconds": avg_duration,
        "average_observations_per_track": avg_obs,
        "most_frequently_tracked_class": most_frequent,
    }


def get_tracked_objects(
    db: Session,
    job_id: str,
    user_id: str,
    class_name: Optional[str] = None,
    min_duration: Optional[float] = None,
) -> List[TrackedObject]:
    """
    Retrieve tracked objects for a job with optional class and duration filtering.
    Results ordered by track_id ascending.
    """
    _assert_job_access(db, job_id, user_id)

    tracks = (
        db.query(TrackedObject)
        .filter(TrackedObject.analysis_job_id == job_id)
        .order_by(TrackedObject.track_id.asc())
        .all()
    )

    if class_name:
        cls_filter = class_name.lower().strip()
        tracks = [t for t in tracks if t.class_name == cls_filter]

    if min_duration is not None:
        tracks = [
            t for t in tracks
            if (t.last_seen_timestamp - t.first_seen_timestamp) >= min_duration
        ]

    return tracks


def get_track_detail(
    db: Session,
    job_id: str,
    track_id: int,
    user_id: str,
) -> dict:
    """
    Retrieve full track detail including trajectory points and movement metrics.

    Returns:
        Dict with track metadata, trajectory list, displacement and distance.
    """
    _assert_job_access(db, job_id, user_id)

    track: Optional[TrackedObject] = (
        db.query(TrackedObject)
        .filter(
            TrackedObject.analysis_job_id == job_id,
            TrackedObject.track_id == track_id,
        )
        .first()
    )

    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track #{track_id} not found in this analysis job.",
        )

    points: List[TrackPoint] = track.points  # ordered by frame_index asc

    trajectory = [
        {
            "frame_index": p.frame_index,
            "timestamp_seconds": round(p.timestamp_seconds, 3),
            "center_x": round(p.center_x, 2),
            "center_y": round(p.center_y, 2),
            "x1": p.x1,
            "y1": p.y1,
            "x2": p.x2,
            "y2": p.y2,
            "confidence": round(p.confidence, 4),
        }
        for p in points
    ]

    # Movement metrics
    centers = [(p.center_x, p.center_y) for p in points]
    displacement = 0.0
    trajectory_distance = 0.0
    if len(centers) >= 2:
        displacement = round(calculate_displacement(centers[0], centers[-1]), 2)
        trajectory_distance = round(calculate_trajectory_distance(centers), 2)

    duration_seconds = round(
        track.last_seen_timestamp - track.first_seen_timestamp, 2
    )

    return {
        "id": track.id,
        "track_id": track.track_id,
        "class_id": track.class_id,
        "class_name": track.class_name,
        "first_seen_timestamp": round(track.first_seen_timestamp, 3),
        "last_seen_timestamp": round(track.last_seen_timestamp, 3),
        "duration_seconds": duration_seconds,
        "first_seen_frame": track.first_seen_frame,
        "last_seen_frame": track.last_seen_frame,
        "total_frames": track.total_frames,
        "average_confidence": round(track.average_confidence, 4),
        "max_confidence": round(track.max_confidence, 4),
        "displacement_pixels": displacement,
        "trajectory_distance_pixels": trajectory_distance,
        "trajectory": trajectory,
    }
