import datetime
import logging
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.events.publisher import get_event_publisher
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.camera import Camera
from app.models.detection import Detection
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.models.security_rule import SecurityRule
from app.models.track_point import TrackPoint
from app.models.tracked_object import TrackedObject
from app.vision.detection.yolo_detector import YOLODetector
from app.vision.events.engine import EventEngine
from app.vision.events.rules import RuleDefinition
from app.vision.frame_extractor import save_frame_and_thumbnail
from app.vision.frame_sampler import FrameSampler
from app.vision.tracking.track_manager import get_track_manager
from app.vision.tracking.trajectory import calculate_center
from app.vision.video_reader import VideoReader

logger = logging.getLogger("sentinel.services.realtime")


class RealtimeStatus:
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class RealtimeSession:
    """Represents an active in-memory real-time video monitoring session."""

    def __init__(
        self,
        job_id: str,
        user_id: str,
        camera_id: Optional[str] = None,
        camera_name: Optional[str] = None,
    ):
        self.job_id = job_id
        self.user_id = user_id
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.status = RealtimeStatus.CREATED
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.current_timestamp: float = 0.0
        self.frames_processed: int = 0
        self.processing_fps: float = 0.0
        self.active_tracks: int = 0
        self.active_tracks_list: List[Dict[str, Any]] = []
        self.events_detected: int = 0
        self.last_heartbeat: str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.latest_frame_path: Optional[str] = None
        self.latest_annotated_frame_path: Optional[str] = None
        self.latest_frame_index: Optional[int] = None
        self.error_message: Optional[str] = None
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "current_timestamp": round(self.current_timestamp, 2),
            "frames_processed": self.frames_processed,
            "processing_fps": round(self.processing_fps, 1),
            "active_tracks": self.active_tracks,
            "active_tracks_list": self.active_tracks_list,
            "events_detected": self.events_detected,
            "last_heartbeat": self.last_heartbeat,
            "latest_frame_index": self.latest_frame_index,
            "error_message": self.error_message,
        }


class RealtimeSessionManager:
    """
    Manages the lifecycle of real-time monitoring sessions in-memory.
    Ensures safe start, stop, conflict prevention, and resource disposal.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, RealtimeSession] = {}

    def get_session(self, job_id: str) -> Optional[RealtimeSession]:
        with self._lock:
            return self._sessions.get(job_id)

    def get_session_status(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        session = self.get_session(job_id)
        if session and session.user_id == user_id:
            return session.to_dict()
        return None

    def get_active_sessions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            active = [
                s.to_dict()
                for s in self._sessions.values()
                if s.user_id == user_id
                and s.status in (RealtimeStatus.STARTING, RealtimeStatus.RUNNING, RealtimeStatus.PAUSED)
            ]
        return active

    def start_session(self, job_id: str, user_id: str, db: Session) -> RealtimeSession:
        """Start or resume a real-time monitoring session for a job."""
        with self._lock:
            existing = self._sessions.get(job_id)
            if existing and existing.status in (RealtimeStatus.STARTING, RealtimeStatus.RUNNING):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A real-time monitoring session is already running for this job.",
                )

        # Validate job existence and ownership
        job = (
            db.query(AnalysisJob)
            .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
            .first()
        )
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis job not found or access denied.",
            )

        # Fetch camera name if camera is attached
        camera_name = None
        if job.camera_id:
            cam = db.query(Camera.name).filter(Camera.id == job.camera_id).first()
            if cam:
                camera_name = cam[0]

        session = RealtimeSession(
            job_id=job.id,
            user_id=user_id,
            camera_id=job.camera_id,
            camera_name=camera_name,
        )
        session.status = RealtimeStatus.STARTING
        session.start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._lock:
            self._sessions[job_id] = session

        # Start monitoring worker thread
        thread = threading.Thread(
            target=self._run_monitoring_loop,
            args=(session, job.source_path),
            daemon=True,
            name=f"realtime-monitor-{job_id[:8]}",
        )
        session.thread = thread
        thread.start()

        logger.info(f"Realtime monitoring session started for job {job_id}")
        return session

    def stop_session(self, job_id: str, user_id: str) -> RealtimeSession:
        """Signal a running session to gracefully stop and finalize resources."""
        session = self.get_session(job_id)
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active monitoring session not found for this job.",
            )

        if session.status in (RealtimeStatus.STOPPED, RealtimeStatus.COMPLETED, RealtimeStatus.FAILED):
            return session

        session.status = RealtimeStatus.STOPPING
        session.stop_event.set()

        # Notify subscribers of stopping state
        publisher = get_event_publisher()
        publisher.publish_status(job_id, user_id, session.to_dict())

        # Wait briefly for thread to finish safe cleanup
        if session.thread and session.thread.is_alive():
            session.thread.join(timeout=3.0)

        session.status = RealtimeStatus.STOPPED
        session.end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        publisher.publish_status(job_id, user_id, session.to_dict())

        logger.info(f"Realtime monitoring session stopped for job {job_id}")
        return session

    def _run_monitoring_loop(self, session: RealtimeSession, video_path: str) -> None:
        """
        Background monitoring processing loop:
        Decodes video frames, runs YOLO + ByteTrack + EventEngine,
        persists events immediately to DB, and broadcasts events & status via WebSocket.
        """
        job_id = session.job_id
        user_id = session.user_id
        publisher = get_event_publisher()

        db = SessionLocal()
        detector: Optional[YOLODetector] = None
        event_engine: Optional[EventEngine] = None
        last_status_broadcast = 0.0

        try:
            # Update AnalysisJob status in DB
            db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if db_job:
                db_job.status = JobStatus.PROCESSING
                db_job.started_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()

            # Initialize YOLO Detector
            try:
                detector = YOLODetector(
                    model_name=settings.YOLO_MODEL,
                    confidence_threshold=settings.YOLO_CONFIDENCE_THRESHOLD,
                    allowed_classes=settings.allowed_classes_list,
                    device=settings.YOLO_DEVICE,
                )
            except Exception as e:
                logger.warning(f"Failed to load YOLO model for realtime session {job_id}: {e}")

            # Initialize Tracker
            track_manager = get_track_manager()
            tracker = track_manager.create_tracker(job_id)

            # Load active Security Rules for EventEngine
            db_rules = (
                db.query(SecurityRule)
                .filter(
                    SecurityRule.user_id == user_id,
                    SecurityRule.is_enabled == True,
                )
                .all()
            )
            applicable_rules = []
            for r in db_rules:
                if r.camera_id is None or r.camera_id == session.camera_id:
                    applicable_rules.append(RuleDefinition.from_orm(r))

            event_engine = EventEngine(rules=applicable_rules)

            # Prepare storage directories
            job_frames_dir = os.path.join(settings.frames_path, job_id)
            job_annotated_dir = os.path.join(settings.annotated_path, job_id)
            os.makedirs(job_frames_dir, exist_ok=True)
            os.makedirs(job_annotated_dir, exist_ok=True)

            # Trajectory buffer & track history
            trajectory_buffer: Dict[int, List] = {}
            history_for_events: Dict[int, List] = {}
            # track candidate dedup_key -> database SecurityEvent.id
            emitted_event_db_ids: Dict[str, str] = {}

            session.status = RealtimeStatus.RUNNING
            publisher.publish_status(job_id, user_id, session.to_dict())

            loop_start_time = time.time()
            frames_counted = 0

            with VideoReader(video_path) as reader:
                metadata = reader.metadata
                sampler = FrameSampler(
                    fps=metadata.fps,
                    total_frames=metadata.frame_count,
                    interval_seconds=settings.SAMPLE_INTERVAL_SECONDS,
                )

                for frame_index, frame in reader.iter_frames():
                    if session.stop_event.is_set():
                        logger.info(f"Stop signal received for session {job_id}")
                        break

                    if not sampler.should_sample(frame_index):
                        continue

                    timestamp = sampler.timestamp_for_frame(frame_index)
                    frame_start = time.time()

                    # Trajectory snapshot for annotation
                    max_traj_points = settings.TRACK_MAX_TRAJECTORY_POINTS
                    traj_for_annotation = {
                        tid: list(pts[-max_traj_points:])
                        for tid, pts in trajectory_buffer.items()
                        if pts
                    }

                    frame_info = save_frame_and_thumbnail(
                        frame=frame,
                        output_dir=job_frames_dir,
                        frame_index=frame_index,
                        timestamp_seconds=timestamp,
                        max_frame_width=settings.MAX_FRAME_WIDTH,
                        thumbnail_width=settings.THUMBNAIL_WIDTH,
                        detector=detector,
                        tracker=tracker,
                        annotated_dir=job_annotated_dir,
                        trajectories=traj_for_annotation,
                    )

                    # Persist AnalysisResult for the sampled frame
                    result = AnalysisResult(
                        analysis_job_id=job_id,
                        frame_index=frame_index,
                        timestamp_seconds=timestamp,
                        frame_path=frame_info.frame_path,
                        thumbnail_path=frame_info.thumbnail_path,
                        annotated_frame_path=frame_info.annotated_frame_path,
                        detection_count=len(frame_info.detections),
                        width=frame_info.width,
                        height=frame_info.height,
                        processing_time_ms=frame_info.processing_time_ms,
                    )
                    db.add(result)
                    db.flush()

                    frame_tracks = []
                    active_track_details = []

                    for det in frame_info.detections:
                        det_rec = Detection(
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
                        db.add(det_rec)

                        if det.track_id is not None:
                            tid = det.track_id
                            cx, cy = calculate_center(det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2)

                            if tid not in trajectory_buffer:
                                trajectory_buffer[tid] = []
                            trajectory_buffer[tid].append((cx, cy))
                            if len(trajectory_buffer[tid]) > max_traj_points * 2:
                                trajectory_buffer[tid] = trajectory_buffer[tid][-max_traj_points:]

                            tdict = {
                                "track_id": tid,
                                "class_name": det.class_name,
                                "confidence": det.confidence,
                                "center_x": cx,
                                "center_y": cy,
                                "x1": det.bbox.x1,
                                "y1": det.bbox.y1,
                                "x2": det.bbox.x2,
                                "y2": det.bbox.y2,
                                "timestamp_seconds": timestamp,
                                "frame_index": frame_index,
                            }
                            frame_tracks.append(tdict)

                            if tid not in history_for_events:
                                history_for_events[tid] = []
                            history_for_events[tid].append(tdict)

                            active_track_details.append({
                                "track_id": tid,
                                "class_name": det.class_name,
                                "confidence": round(det.confidence, 2),
                                "duration_seconds": round(timestamp - history_for_events[tid][0]["timestamp_seconds"], 1),
                            })

                    # Evaluate Security Events for this frame
                    candidates = event_engine.process_frame(
                        frame_index=frame_index,
                        timestamp_seconds=timestamp,
                        result_id=result.id,
                        tracks=frame_tracks,
                        trajectory_history=history_for_events,
                        frame_width=frame_info.width,
                        frame_height=frame_info.height,
                    )

                    # ── PERSIST FIRST, THEN BROADCAST ──
                    for cand in candidates:
                        if cand.dedup_key in emitted_event_db_ids:
                            # Event already exists in DB — UPDATE IT
                            db_event_id = emitted_event_db_ids[cand.dedup_key]
                            existing_ev = db.query(SecurityEvent).filter(SecurityEvent.id == db_event_id).first()
                            if existing_ev:
                                existing_ev.end_timestamp = cand.end_timestamp
                                existing_ev.duration_seconds = cand.duration_seconds
                                existing_ev.confidence = cand.confidence
                                existing_ev.metadata_json = cand.metadata
                                db.commit()

                                # Publish update message
                                event_payload = {
                                    "id": existing_ev.id,
                                    "analysis_job_id": job_id,
                                    "camera_id": session.camera_id,
                                    "camera_name": session.camera_name,
                                    "rule_id": cand.rule_id,
                                    "event_type": cand.event_type,
                                    "severity": cand.severity,
                                    "status": existing_ev.status.value if hasattr(existing_ev.status, 'value') else existing_ev.status,
                                    "title": cand.title,
                                    "description": cand.description,
                                    "start_timestamp": round(cand.start_timestamp, 2),
                                    "end_timestamp": round(cand.end_timestamp, 2) if cand.end_timestamp is not None else None,
                                    "duration_seconds": round(cand.duration_seconds, 1) if cand.duration_seconds is not None else None,
                                    "confidence": round(cand.confidence, 2) if cand.confidence is not None else None,
                                    "track_id": cand.track_id,
                                    "class_name": cand.class_name,
                                    "metadata": cand.metadata,
                                }
                                publisher.publish("event_updated", event_payload, job_id, user_id)
                        else:
                            # Brand new event candidate — PERSIST TO DATABASE
                            new_event_id = str(uuid.uuid4())
                            sec_ev = SecurityEvent(
                                id=new_event_id,
                                analysis_job_id=job_id,
                                camera_id=session.camera_id,
                                rule_id=cand.rule_id,
                                track_id=cand.track_id,
                                class_name=cand.class_name,
                                event_type=cand.event_type,
                                severity=cand.severity,
                                status=SecurityEventStatus.OPEN,
                                title=cand.title,
                                description=cand.description,
                                start_timestamp=cand.start_timestamp,
                                end_timestamp=cand.end_timestamp,
                                duration_seconds=cand.duration_seconds,
                                confidence=cand.confidence,
                                evidence_frame_id=result.id,
                                metadata_json=cand.metadata,
                            )
                            db.add(sec_ev)
                            db.commit()

                            emitted_event_db_ids[cand.dedup_key] = new_event_id
                            session.events_detected += 1

                            # Publish new event message
                            event_payload = {
                                "id": new_event_id,
                                "analysis_job_id": job_id,
                                "camera_id": session.camera_id,
                                "camera_name": session.camera_name,
                                "rule_id": cand.rule_id,
                                "event_type": cand.event_type,
                                "severity": cand.severity,
                                "status": "OPEN",
                                "title": cand.title,
                                "description": cand.description,
                                "start_timestamp": round(cand.start_timestamp, 2),
                                "end_timestamp": round(cand.end_timestamp, 2) if cand.end_timestamp is not None else None,
                                "duration_seconds": round(cand.duration_seconds, 1) if cand.duration_seconds is not None else None,
                                "confidence": round(cand.confidence, 2) if cand.confidence is not None else None,
                                "evidence_frame_url": f"/api/video-analysis/{job_id}/frames/{frame_index}",
                                "track_id": cand.track_id,
                                "class_name": cand.class_name,
                                "metadata": cand.metadata,
                            }
                            publisher.publish("security_event", event_payload, job_id, user_id)

                    # Update session telemetry metrics
                    frames_counted += 1
                    session.frames_processed = frames_counted
                    session.current_timestamp = timestamp
                    session.active_tracks = len(frame_tracks)
                    session.active_tracks_list = active_track_details
                    session.latest_frame_path = frame_info.frame_path
                    session.latest_annotated_frame_path = frame_info.annotated_frame_path
                    session.latest_frame_index = frame_index
                    session.last_heartbeat = datetime.datetime.now(datetime.timezone.utc).isoformat()

                    elapsed_total = time.time() - loop_start_time
                    if elapsed_total > 0:
                        session.processing_fps = frames_counted / elapsed_total

                    # Throttle real-time status broadcast (max 2-3 per second)
                    now = time.time()
                    if now - last_status_broadcast >= 0.4:
                        last_status_broadcast = now
                        publisher.publish_status(job_id, user_id, session.to_dict())

                    # Optional: slight pacing delay so video simulates real-time stream progression
                    processing_cost = time.time() - frame_start
                    desired_pace = 0.2  # 5 samples per second max playback speed
                    if processing_cost < desired_pace:
                        time.sleep(desired_pace - processing_cost)

            # Finalize EventEngine on loop end
            final_time = session.current_timestamp
            final_events = event_engine.finalize(final_time)
            for cand in final_events:
                if cand.dedup_key in emitted_event_db_ids:
                    db_event_id = emitted_event_db_ids[cand.dedup_key]
                    ev = db.query(SecurityEvent).filter(SecurityEvent.id == db_event_id).first()
                    if ev:
                        ev.end_timestamp = cand.end_timestamp
                        ev.duration_seconds = cand.duration_seconds
                        ev.confidence = cand.confidence
                        db.commit()

            # Mark session and job completed/stopped
            final_status = RealtimeStatus.STOPPED if session.stop_event.is_set() else RealtimeStatus.COMPLETED
            session.status = final_status
            session.end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

            db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if db_job:
                db_job.status = JobStatus.COMPLETED if final_status == RealtimeStatus.COMPLETED else JobStatus.CANCELLED
                db_job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db_job.processed_frames = session.frames_processed
                db_job.progress = 100 if final_status == RealtimeStatus.COMPLETED else db_job.progress
                db.commit()

            publisher.publish_status(job_id, user_id, session.to_dict())
            logger.info(f"Realtime loop finished for job {job_id} with status {final_status}")

        except Exception as e:
            logger.error(f"Error in realtime monitoring loop for job {job_id}: {e}", exc_info=True)
            session.status = RealtimeStatus.FAILED
            session.error_message = str(e)
            session.end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            publisher.publish_status(job_id, user_id, session.to_dict())

            try:
                db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
                if db_job:
                    db_job.status = JobStatus.FAILED
                    db_job.error_message = str(e)
                    db.commit()
            except Exception:
                pass

        finally:
            # Release resources
            get_track_manager().close_tracker(job_id)
            db.close()


_global_realtime_manager: Optional[RealtimeSessionManager] = None
_realtime_manager_lock = threading.Lock()


def get_realtime_session_manager() -> RealtimeSessionManager:
    """Retrieve or initialize the singleton RealtimeSessionManager."""
    global _global_realtime_manager
    if _global_realtime_manager is None:
        with _realtime_manager_lock:
            if _global_realtime_manager is None:
                _global_realtime_manager = RealtimeSessionManager()
    return _global_realtime_manager
