import logging
import os
from pathlib import Path
from typing import List, Optional, Set

import numpy as np

from app.core.config import settings
from app.vision.detection.detector import BoundingBox, DetectionResult
from app.vision.detection.model_manager import YOLOModelManager, get_model_manager
from app.vision.tracking.tracker import ObjectTracker

logger = logging.getLogger("sentinel.vision.tracking.bytetrack")


class ByteTrackTracker(ObjectTracker):
    """
    ByteTrack implementation for multi-object tracking in surveillance video streams.
    Integrates with Ultralytics YOLO while guaranteeing job-isolated tracker states,
    confidence filtering, security whitelist classes, and fallback resilience.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        allowed_classes: Optional[List[str]] = None,
        tracker_config_path: Optional[str] = None,
        model_manager: Optional[YOLOModelManager] = None,
    ):
        self.model_name = model_name or settings.YOLO_MODEL
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.YOLO_CONFIDENCE_THRESHOLD
        )

        if allowed_classes is not None:
            self.allowed_classes: Optional[Set[str]] = {
                c.strip().lower() for c in allowed_classes if c.strip()
            }
        else:
            raw_allowed = settings.allowed_classes_list
            self.allowed_classes = {c.lower() for c in raw_allowed} if raw_allowed else None

        # Resolve bytetrack config path
        if tracker_config_path and os.path.exists(tracker_config_path):
            self.tracker_config = tracker_config_path
        else:
            default_config = Path(__file__).parent / "configs" / "bytetrack.yaml"
            if default_config.exists():
                self.tracker_config = str(default_config)
            else:
                self.tracker_config = "bytetrack.yaml"

        self.model_manager = model_manager or get_model_manager()
        self.device = self.model_manager._device or "cpu"

        # Ensure fresh state on instantiation
        self.reset()

    def track(
        self,
        frame: np.ndarray,
        frame_index: int = 0,
        timestamp_seconds: float = 0.0,
    ) -> List[DetectionResult]:
        """
        Track objects on a single video frame, associating detections across time.

        Args:
            frame: np.ndarray BGR image matrix.
            frame_index: Sequential index of frame.
            timestamp_seconds: Video timestamp in seconds.

        Returns:
            List of DetectionResult objects with track_id populated.
        """
        if frame is None or frame.size == 0:
            return []

        model = self.model_manager.get_model(self.model_name)
        names_dict = getattr(model, "names", {})

        detections: List[DetectionResult] = []

        try:
            results = model.track(
                source=frame,
                persist=True,
                tracker=self.tracker_config,
                conf=self.confidence_threshold,
                verbose=False,
                device=self.device,
            )
        except Exception as e:
            logger.warning(
                f"Tracking exception on frame {frame_index} (t={timestamp_seconds:.2f}s): {e}. "
                f"Gracefully falling back to detection without tracks."
            )
            try:
                results = model.predict(
                    source=frame,
                    conf=self.confidence_threshold,
                    verbose=False,
                    device=self.device,
                )
            except Exception as predict_err:
                logger.error(f"Inference fallback also failed on frame {frame_index}: {predict_err}")
                return []

        if not results:
            return detections

        first_result = results[0]
        boxes = first_result.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            conf = float(box.conf[0].item()) if hasattr(box.conf[0], "item") else float(box.conf[0])
            if conf < self.confidence_threshold:
                continue

            cls_id = int(box.cls[0].item()) if hasattr(box.cls[0], "item") else int(box.cls[0])
            cls_name = names_dict.get(cls_id, str(cls_id)).lower()

            if self.allowed_classes and cls_name not in self.allowed_classes:
                continue

            # Extract track_id if available
            track_id: Optional[int] = None
            if hasattr(box, "id") and box.id is not None:
                try:
                    val = box.id[0].item() if hasattr(box.id[0], "item") else box.id[0]
                    track_id = int(val)
                except (IndexError, TypeError, ValueError):
                    track_id = None

            # Extract bounding box coordinates [x1, y1, x2, y2]
            xyxy = box.xyxy[0]
            if hasattr(xyxy, "tolist"):
                coords = xyxy.tolist()
            else:
                coords = [float(x) for x in xyxy]

            bbox = BoundingBox.from_coords(coords[0], coords[1], coords[2], coords[3])

            detections.append(
                DetectionResult(
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=round(conf, 4),
                    bbox=bbox,
                    track_id=track_id,
                )
            )

        return detections

    def reset(self) -> None:
        """
        Reset tracker internal state, trajectory cache, and track ID counter.
        Guarantees that track IDs start independently for each analysis job.
        """
        try:
            model = self.model_manager.get_model(self.model_name)
            if hasattr(model, "predictor") and model.predictor is not None:
                model.predictor.trackers = None
        except Exception as e:
            logger.debug(f"Predictor reset notice: {e}")

        try:
            from ultralytics.trackers.byte_tracker import BYTETracker
            BYTETracker.reset_id()
        except Exception as e:
            logger.debug(f"BYTETracker reset_id notice: {e}")

        logger.debug("ByteTrackTracker state and IDs reset successfully.")
