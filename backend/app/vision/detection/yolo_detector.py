import logging
from typing import List, Optional, Set

import numpy as np

from app.core.config import settings
from app.vision.detection.detector import BoundingBox, DetectionResult, ObjectDetector
from app.vision.detection.model_manager import YOLOModelManager, get_model_manager

logger = logging.getLogger("sentinel.vision.detection.yolo_detector")


class YOLODetector(ObjectDetector):
    """
    Concrete ObjectDetector implementation powered by Ultralytics YOLO.
    Performs frame inference, extracts bounding boxes, and applies confidence & class filters.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        allowed_classes: Optional[List[str]] = None,
        model_manager: Optional[YOLOModelManager] = None,
    ):
        self.model_name = model_name or settings.YOLO_MODEL
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.YOLO_CONFIDENCE_THRESHOLD
        )
        # Convert allowed classes to lowercase set for O(1) lookup
        if allowed_classes is not None:
            self.allowed_classes: Optional[Set[str]] = {
                c.strip().lower() for c in allowed_classes if c.strip()
            }
        else:
            raw_allowed = settings.allowed_classes_list
            self.allowed_classes = {c.lower() for c in raw_allowed} if raw_allowed else None

        self.model_manager = model_manager or get_model_manager()

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Run YOLO inference on a single BGR OpenCV frame.

        Args:
            frame: np.ndarray image matrix (H, W, 3).

        Returns:
            List of valid, filtered DetectionResult objects.
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty frame passed to YOLODetector. Returning 0 detections.")
            return []

        # Get cached model
        model = self.model_manager.get_model(self.model_name)

        # Run inference with verbose=False for clean logs and CPU-friendly execution
        results = model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
            device=self.model_manager._device or "cpu",
        )

        detections: List[DetectionResult] = []

        if not results:
            return detections

        first_result = results[0]
        boxes = first_result.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        # Extract names dictionary from model
        names_dict = getattr(model, "names", {})

        for box in boxes:
            conf = float(box.conf[0].item()) if hasattr(box.conf[0], "item") else float(box.conf[0])
            if conf < self.confidence_threshold:
                continue

            cls_id = int(box.cls[0].item()) if hasattr(box.cls[0], "item") else int(box.cls[0])
            cls_name = names_dict.get(cls_id, str(cls_id)).lower()

            # Apply class filter if configured
            if self.allowed_classes and cls_name not in self.allowed_classes:
                continue

            # Extract coordinates [x1, y1, x2, y2]
            xyxy = box.xyxy[0].tolist()
            bbox = BoundingBox.from_coords(xyxy[0], xyxy[1], xyxy[2], xyxy[3])

            detections.append(
                DetectionResult(
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=round(conf, 4),
                    bbox=bbox,
                )
            )

        return detections
