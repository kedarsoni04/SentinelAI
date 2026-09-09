from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class BoundingBox:
    """Bounding box coordinates referring to the processed frame coordinate system."""
    x1: int
    y1: int
    x2: int
    y2: int
    width: int
    height: int

    @classmethod
    def from_coords(cls, x1: float, y1: float, x2: float, y2: float) -> "BoundingBox":
        ix1 = int(round(x1))
        iy1 = int(round(y1))
        ix2 = int(round(x2))
        iy2 = int(round(y2))
        return cls(
            x1=ix1,
            y1=iy1,
            x2=ix2,
            y2=iy2,
            width=max(0, ix2 - ix1),
            height=max(0, iy2 - iy1),
        )


@dataclass
class DetectionResult:
    """Individual object detection result, optionally associated with a track ID."""
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None


class ObjectDetector(ABC):
    """
    Abstract interface for object detection engines.
    Decouples the video processing pipeline from specific ML model frameworks.
    """

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Execute object detection on a single image frame (BGR format).

        Args:
            frame: OpenCV image array (H, W, C) in BGR color space.

        Returns:
            List of valid, filtered DetectionResult objects.
        """
        pass
