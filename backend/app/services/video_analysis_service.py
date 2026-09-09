import logging
import os
import shutil
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.detection import Detection
from app.models.security_event import SecurityEvent
from app.models.security_rule import SecurityRule
from app.models.track_point import TrackPoint
from app.models.tracked_object import TrackedObject
from app.vision.analyzer import VideoAnalyzer
from app.vision.detection.yolo_detector import YOLODetector
from app.vision.events.engine import EventEngine
from app.vision.events.rules import RuleDefinition
from app.vision.tracking.track_manager import get_track_manager
from app.vision.tracking.trajectory import calculate_center

logger = logging.getLogger("sentinel.services.video_analysis")

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def validate_video_file(file: UploadFile) -> str:
    """
    Validate uploaded video file extension and MIME type.
    Returns the normalized extension if valid, raises HTTPException otherwise.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing.",
        )

    _, ext = os.path.splitext(file.filename)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported video format '{ext}'. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # Validate MIME type where provided
    if file.content_type and not (
        file.content_type.startswith("video/") or file.content_type == "application/octet-stream"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content-type: {file.content_type}",
        )

    return ext_lower


def save_uploaded_file(file: UploadFile, user_id: str) -> Tuple[str, str]:
    """
    Safely stream the uploaded video to the local storage directory.
    Enforces maximum upload file size and uses a UUID-based internal filename.

    Returns:
        Tuple of (saved_file_path, original_filename)
    """
    ext = validate_video_file(file)
    original_filename = os.path.basename(file.filename or "video.mp4")

    # Generate safe unique internal filename
    file_uuid = str(uuid.uuid4())
    internal_filename = f"{file_uuid}{ext}"
    dest_path = os.path.join(settings.uploads_path, internal_filename)

    max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    bytes_written = 0

    try:
        with open(dest_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)  # 1MB chunk
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    buffer.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Video file exceeds maximum size limit of {settings.MAX_VIDEO_SIZE_MB} MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream upload to disk: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded video to storage.",
        )

    logger.info(
        f"Saved upload '{original_filename}' as '{internal_filename}' "
        f"({bytes_written / (1024*1024):.2f} MB)"
    )
    return dest_path, original_filename


def create_analysis_job(
    db: Session,
    user_id: str,
    source_path: str,
    original_filename: str,
    camera_id: Optional[str] = None,
) -> AnalysisJob:
    """Insert a new QUEUED analysis job in the database."""
    job = AnalysisJob(
        user_id=user_id,
        camera_id=camera_id,
        source_type="VIDEO_FILE",
        source_path=source_path,
        original_filename=original_filename,
        status=JobStatus.QUEUED,
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"Created analysis job {job.id} for user {user_id}")
    return job


def run_analysis_pipeline_background(job_id: str) -> None:
    """
    Background worker task: executes the OpenCV processing pipeline.
    Runs in an independent database session for non-blocking execution.
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"Background worker: job {job_id} not found.")
            return

        if job.status == JobStatus.CANCELLED:
            logger.info(f"Background worker: job {job_id} was cancelled before starting.")
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        job.progress = 5
        db.commit()

        job_frames_dir = os.path.join(settings.frames_path, job_id)
        os.makedirs(job_frames_dir, exist_ok=True)
        job_annotated_dir = os.path.join(settings.annotated_path, job_id)
        os.makedirs(job_annotated_dir, exist_ok=True)

        # Initialize Object Tracker (wraps YOLO + ByteTrack) or fallback Detector
        tracker = None
        detector = None
        track_manager = get_track_manager()

        if settings.TRACKING_ENABLED:
            try:
                tracker = track_manager.create_tracker(job_id)
                logger.info(f"Initialized tracker '{settings.TRACKER_TYPE}' for job {job_id}")
            except Exception as ex:
                logger.warning(f"Tracker init failed for job {job_id}: {ex}. Falling back to detection only.")
                tracker = None

        if tracker is None:
            try:
                detector = YOLODetector()
            except Exception as ex:
                logger.error(f"Failed to initialize YOLO detector for job {job_id}: {ex}")
                job.status = JobStatus.FAILED
                job.error_message = "AI detection engine failed to initialize."
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
                return

        analyzer = VideoAnalyzer(
            video_path=job.source_path,
            output_dir=job_frames_dir,
            interval_seconds=settings.SAMPLE_INTERVAL_SECONDS,
            max_frame_width=settings.MAX_FRAME_WIDTH,
            thumbnail_width=settings.THUMBNAIL_WIDTH,
            detector=detector,
            tracker=tracker,
            annotated_dir=job_annotated_dir,
        )

        last_progress = [5]

        def on_progress(processed_count: int, planned_count: int, pct: int):
            # Batch progress updates to avoid saturating SQLite commits
            if pct - last_progress[0] >= 10 or pct >= 95:
                last_progress[0] = pct
                try:
                    job.progress = pct
                    job.processed_frames = processed_count
                    db.commit()
                except Exception as ex:
                    logger.debug(f"Progress commit error: {ex}")

        def is_cancelled() -> bool:
            # Re-check database state for cancellation flag
            current = db.query(AnalysisJob.status).filter(AnalysisJob.id == job_id).first()
            return bool(current and current[0] == JobStatus.CANCELLED)

        # Run OpenCV decoding + frame sampling + YOLO detection + frame annotation
        metadata, extracted_frames = analyzer.run(
            progress_callback=on_progress,
            is_cancelled_callback=is_cancelled,
        )

        # Check if cancelled during run
        db.refresh(job)
        if job.status == JobStatus.CANCELLED:
            logger.info(f"Job {job_id} was cancelled during frame processing.")
            return

        # ── Phase 6: Load enabled security rules & initialize EventEngine ───────
        db_rules = (
            db.query(SecurityRule)
            .filter(
                SecurityRule.user_id == job.user_id,
                SecurityRule.is_enabled == True,
            )
            .all()
        )
        # Filter rules applicable to this job: camera-specific match or camera-agnostic
        applicable_rules = []
        for r in db_rules:
            if r.camera_id is None or r.camera_id == job.camera_id:
                applicable_rules.append(RuleDefinition.from_orm(r))

        event_engine = EventEngine(rules=applicable_rules)
        logger.info(
            f"Job {job_id}: initialized EventEngine with {len(applicable_rules)} active rules."
        )

        # ── Phase 5: Accumulate tracking data across all frames ─────────────────
        # track_id -> accumulator dict:
        #   class_name, class_id, first_seen_*, last_seen_*, confidences, frames
        track_accumulators: Dict[int, dict] = {}
        # track_id -> list[(analysis_result_id, frame_index, ts, bbox, center_x, center_y, confidence)]
        track_observations: Dict[int, list] = defaultdict(list)
        # track_id -> list of observation dicts for EventEngine
        history_for_events: Dict[int, list] = defaultdict(list)

        # Insert AnalysisResult and Detection records transactionally
        for info in extracted_frames:
            result = AnalysisResult(
                analysis_job_id=job.id,
                frame_index=info.frame_index,
                timestamp_seconds=info.timestamp_seconds,
                frame_path=info.frame_path,
                thumbnail_path=info.thumbnail_path,
                annotated_frame_path=info.annotated_frame_path,
                detection_count=len(info.detections),
                width=info.width,
                height=info.height,
                processing_time_ms=info.processing_time_ms,
            )
            db.add(result)
            db.flush()  # get result.id

            frame_tracks = []

            for det in info.detections:
                det_record = Detection(
                    analysis_result_id=result.id,
                    class_id=det.class_id,
                    class_name=det.class_name,
                    confidence=det.confidence,
                    x1=det.bbox.x1,
                    y1=det.bbox.y1,
                    x2=det.bbox.x2,
                    y2=det.bbox.y2,
                    width=det.bbox.width,
                    height=det.bbox.height,
                    track_id=det.track_id,
                )
                db.add(det_record)

                # Accumulate track data if this detection belongs to a track
                if det.track_id is not None:
                    tid = det.track_id
                    cx, cy = calculate_center(
                        det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2
                    )

                    track_dict = {
                        "track_id": tid,
                        "class_name": det.class_name,
                        "confidence": det.confidence,
                        "center_x": cx,
                        "center_y": cy,
                        "x1": det.bbox.x1,
                        "y1": det.bbox.y1,
                        "x2": det.bbox.x2,
                        "y2": det.bbox.y2,
                        "timestamp_seconds": info.timestamp_seconds,
                        "frame_index": info.frame_index,
                    }
                    frame_tracks.append(track_dict)
                    history_for_events[tid].append(track_dict)

                    if tid not in track_accumulators:
                        track_accumulators[tid] = {
                            "class_id": det.class_id,
                            "class_name": det.class_name,
                            "first_seen_timestamp": info.timestamp_seconds,
                            "first_seen_frame": info.frame_index,
                            "last_seen_timestamp": info.timestamp_seconds,
                            "last_seen_frame": info.frame_index,
                            "confidences": [det.confidence],
                            "total_frames": 1,
                        }
                    else:
                        acc = track_accumulators[tid]
                        acc["last_seen_timestamp"] = info.timestamp_seconds
                        acc["last_seen_frame"] = info.frame_index
                        acc["confidences"].append(det.confidence)
                        acc["total_frames"] += 1

                    track_observations[tid].append({
                        "result_id": result.id,
                        "frame_index": info.frame_index,
                        "timestamp_seconds": info.timestamp_seconds,
                        "x1": det.bbox.x1,
                        "y1": det.bbox.y1,
                        "x2": det.bbox.x2,
                        "y2": det.bbox.y2,
                        "center_x": cx,
                        "center_y": cy,
                        "width": det.bbox.width,
                        "height": det.bbox.height,
                        "confidence": det.confidence,
                    })

            # ── Phase 6: Evaluate security events for this frame ───────────────
            event_engine.process_frame(
                frame_index=info.frame_index,
                timestamp_seconds=info.timestamp_seconds,
                result_id=result.id,
                tracks=frame_tracks,
                trajectory_history=history_for_events,
                frame_width=info.width,
                frame_height=info.height,
            )

        # ── Phase 5: Persist TrackedObject + TrackPoint records ───────────────────
        track_id_to_db_id: Dict[int, str] = {}
        for tid, acc in track_accumulators.items():
            confidences = acc["confidences"]
            avg_conf = round(sum(confidences) / len(confidences), 4)
            max_conf = round(max(confidences), 4)
            import uuid as _uuid
            tracked_obj = TrackedObject(
                id=str(_uuid.uuid4()),
                analysis_job_id=job.id,
                track_id=tid,
                class_id=acc["class_id"],
                class_name=acc["class_name"],
                first_seen_timestamp=acc["first_seen_timestamp"],
                last_seen_timestamp=acc["last_seen_timestamp"],
                first_seen_frame=acc["first_seen_frame"],
                last_seen_frame=acc["last_seen_frame"],
                total_frames=acc["total_frames"],
                average_confidence=avg_conf,
                max_confidence=max_conf,
            )
            db.add(tracked_obj)
            db.flush()
            track_id_to_db_id[tid] = tracked_obj.id

            for obs in track_observations[tid]:
                tp = TrackPoint(
                    id=str(_uuid.uuid4()),
                    tracked_object_id=tracked_obj.id,
                    analysis_result_id=obs["result_id"],
                    frame_index=obs["frame_index"],
                    timestamp_seconds=obs["timestamp_seconds"],
                    x1=obs["x1"],
                    y1=obs["y1"],
                    x2=obs["x2"],
                    y2=obs["y2"],
                    center_x=obs["center_x"],
                    center_y=obs["center_y"],
                    width=obs["width"],
                    height=obs["height"],
                    confidence=obs["confidence"],
                )
                db.add(tp)

        logger.info(
            f"Job {job_id}: persisted {len(track_accumulators)} tracked objects "
            f"with {sum(len(v) for v in track_observations.values())} total track points."
        )

        # ── Phase 6: Finalize & Persist Security Events ───────────────────────────
        final_video_timestamp = metadata.duration_seconds or (extracted_frames[-1].timestamp_seconds if extracted_frames else 0.0)
        finalized_events = event_engine.finalize(final_video_timestamp)

        for ev in finalized_events:
            tracked_obj_db_id = None
            if ev.track_id is not None and ev.track_id in track_id_to_db_id:
                tracked_obj_db_id = track_id_to_db_id[ev.track_id]

            import uuid as _uuid
            sec_event = SecurityEvent(
                id=str(_uuid.uuid4()),
                analysis_job_id=job.id,
                camera_id=job.camera_id,
                rule_id=ev.rule_id,
                tracked_object_id=tracked_obj_db_id,
                track_id=ev.track_id,
                class_name=ev.class_name,
                event_type=ev.event_type,
                severity=ev.severity,
                title=ev.title,
                description=ev.description,
                start_timestamp=ev.start_timestamp,
                end_timestamp=ev.end_timestamp,
                duration_seconds=ev.duration_seconds,
                confidence=ev.confidence,
                evidence_frame_id=ev.evidence_frame_id,
                metadata_json=ev.metadata,
            )
            db.add(sec_event)

        logger.info(
            f"Job {job_id}: persisted {len(finalized_events)} security events."
        )

        # Finalize job
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.duration_seconds = metadata.duration_seconds
        job.fps = metadata.fps
        job.frame_count = metadata.frame_count
        job.width = metadata.width
        job.height = metadata.height
        job.sampled_frames = len(extracted_frames)
        job.processed_frames = len(extracted_frames)
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None

        db.commit()

        # Release tracker session to free resources and reset state
        if tracker is not None:
            try:
                track_manager.close_tracker(job_id)
            except Exception as e:
                logger.debug(f"Tracker close notice for job {job_id}: {e}")
        logger.info(
            f"Job {job_id} successfully completed: {len(extracted_frames)} frames extracted."
        )

    except Exception as e:
        logger.exception(f"Processing error in job {job_id}: {e}")
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = "Unable to process video: decoding error or invalid stream."
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as commit_err:
            logger.error(f"Failed to record FAILED status for job {job_id}: {commit_err}")
    finally:
        db.close()


def get_user_jobs(db: Session, user_id: str) -> List[AnalysisJob]:
    """Retrieve all analysis jobs created by the authenticated user."""
    return (
        db.query(AnalysisJob)
        .filter(AnalysisJob.user_id == user_id)
        .order_by(AnalysisJob.created_at.desc())
        .all()
    )


def get_job_by_id(db: Session, job_id: str, user_id: str) -> AnalysisJob:
    """
    Retrieve an analysis job by ID, ensuring user ownership.
    Returns 404 if missing or belongs to another user (non-leaking).
    """
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{job_id}' not found.",
        )
    return job


def get_job_results_with_urls(db: Session, job_id: str, user_id: str) -> List[dict]:
    """
    Retrieve frame results for a job, mapping filesystem paths to secure API URLs.
    """
    job = get_job_by_id(db, job_id, user_id)

    results = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.analysis_job_id == job.id)
        .order_by(AnalysisResult.frame_index.asc())
        .all()
    )

    output = []
    for r in results:
        frame_filename = os.path.basename(r.frame_path)
        thumb_filename = os.path.basename(r.thumbnail_path) if r.thumbnail_path else None
        annotated_filename = os.path.basename(r.annotated_frame_path) if r.annotated_frame_path else None

        output.append({
            "id": r.id,
            "analysis_job_id": r.analysis_job_id,
            "frame_index": r.frame_index,
            "timestamp_seconds": r.timestamp_seconds,
            "frame_url": f"/api/video-analysis/{job_id}/frames/{frame_filename}",
            "thumbnail_url": f"/api/video-analysis/{job_id}/frames/{thumb_filename}" if thumb_filename else None,
            "annotated_frame_url": f"/api/video-analysis/{job_id}/annotated/{annotated_filename}" if annotated_filename else None,
            "detection_count": r.detection_count if r.detection_count is not None else 0,
            "width": r.width,
            "height": r.height,
            "processing_time_ms": r.processing_time_ms,
            "created_at": r.created_at,
        })
    return output


def get_frame_path_for_serving(db: Session, job_id: str, filename: str, user_id: str) -> str:
    """
    Resolve and validate a frame file path for HTTP streaming.
    Guarantees user ownership and prevents directory traversal attacks.
    """
    # Enforce job ownership first
    job = get_job_by_id(db, job_id, user_id)

    # Basic filename sanity check
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

    job_frames_dir = os.path.abspath(os.path.join(settings.frames_path, job.id))
    target_path = os.path.abspath(os.path.join(job_frames_dir, filename))

    # Path traversal check
    if not target_path.startswith(job_frames_dir):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to requested file path.",
        )

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Frame file '{filename}' not found.",
        )

    return target_path


def cancel_job(db: Session, job_id: str, user_id: str) -> AnalysisJob:
    """Cancel an active or queued analysis job."""
    job = get_job_by_id(db, job_id, user_id)

    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a job that is already {job.status.value.lower()}.",
        )

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = "Analysis cancelled by operator."
    db.commit()
    db.refresh(job)
    logger.info(f"Job {job_id} marked as CANCELLED by user {user_id}")
    return job


def get_active_jobs_count(db: Session, user_id: str) -> dict:
    """
    Count currently active (QUEUED + PROCESSING) jobs for the SOC dashboard.
    """
    queued = (
        db.query(func.count(AnalysisJob.id))
        .filter(AnalysisJob.user_id == user_id, AnalysisJob.status == JobStatus.QUEUED)
        .scalar()
        or 0
    )
    processing = (
        db.query(func.count(AnalysisJob.id))
        .filter(AnalysisJob.user_id == user_id, AnalysisJob.status == JobStatus.PROCESSING)
        .scalar()
        or 0
    )
    return {
        "active_jobs": queued + processing,
        "queued": queued,
        "processing": processing,
    }
