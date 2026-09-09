import logging
import threading
from typing import Dict, Optional

from app.core.config import settings
from app.vision.tracking.bytetrack_tracker import ByteTrackTracker
from app.vision.tracking.tracker import ObjectTracker

logger = logging.getLogger("sentinel.vision.tracking.manager")


class TrackManager:
    """
    Centralized Tracker Manager.
    Manages tracker instance lifecycles, configuration, and per-job state isolation.
    Ensures that track IDs and internal Kalman filters from one video analysis job
    never contaminate another.
    """

    _instance: Optional["TrackManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._active_trackers: Dict[str, ObjectTracker] = {}
        self._tracker_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "TrackManager":
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def create_tracker(self, job_id: str, tracker_type: Optional[str] = None) -> ObjectTracker:
        """
        Create and initialize a fresh, isolated tracker instance for an analysis job.

        Args:
            job_id: Unique analysis job identifier.
            tracker_type: Tracker algorithm type (defaults to settings.TRACKER_TYPE).

        Returns:
            Configured ObjectTracker instance.
        """
        algo = (tracker_type or settings.TRACKER_TYPE).lower()

        with self._tracker_lock:
            # If an existing tracker was registered for this job, reset it first
            if job_id in self._active_trackers:
                self._active_trackers[job_id].reset()

            if algo == "bytetrack":
                tracker = ByteTrackTracker(
                    model_name=settings.YOLO_MODEL,
                    confidence_threshold=settings.YOLO_CONFIDENCE_THRESHOLD,
                )
            else:
                logger.warning(
                    f"Unknown tracker type '{algo}'. Falling back to default ByteTrack."
                )
                tracker = ByteTrackTracker()

            tracker.reset()
            self._active_trackers[job_id] = tracker
            logger.info(f"Initialized isolated tracker '{algo}' for job {job_id}")
            return tracker

    def has_tracker(self, job_id: str) -> bool:
        """Check if an active tracker exists for the given job."""
        with self._tracker_lock:
            return job_id in self._active_trackers

    def get_tracker(self, job_id: str) -> Optional[ObjectTracker]:
        """Retrieve the active tracker instance for a job if one exists."""
        with self._tracker_lock:
            return self._active_trackers.get(job_id)

    def close_tracker(self, job_id: str) -> None:
        """
        Teardown tracker session and purge all state associated with the job.
        """
        with self._tracker_lock:
            tracker = self._active_trackers.pop(job_id, None)
            if tracker:
                try:
                    tracker.reset()
                except Exception as e:
                    logger.debug(f"Tracker teardown notice for job {job_id}: {e}")
                logger.info(f"Released tracker session for job {job_id}")


def get_track_manager() -> TrackManager:
    """Convenience accessor for global TrackManager."""
    return TrackManager.get_instance()
