from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

from app.vision.detection.detector import BoundingBox, DetectionResult


@dataclass
class TrackedDetection:
    """
    Representation of an object observation with persistent track identity.
    Preserves detection geometry and links to temporal tracking metadata.
    """
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    center_x: float
    center_y: float

    @classmethod
    def from_detection(cls, det: DetectionResult, track_id: int) -> "TrackedDetection":
        cx = (det.bbox.x1 + det.bbox.x2) / 2.0
        cy = (det.bbox.y1 + det.bbox.y2) / 2.0
        return cls(
            track_id=track_id,
            class_id=det.class_id,
            class_name=det.class_name,
            confidence=det.confidence,
            bbox=det.bbox,
            center_x=cx,
            center_y=cy,
        )

    def to_detection_result(self) -> DetectionResult:
        """Convert back to DetectionResult with track_id populated."""
        return DetectionResult(
            class_id=self.class_id,
            class_name=self.class_name,
            confidence=self.confidence,
            bbox=self.bbox,
            track_id=self.track_id,
        )


class ObjectTracker(ABC):
    """
    Abstract interface for object tracking engines.
    Enforces per-job tracking lifecycle, chronological frame processing,
    and decoupling from specific tracking algorithms (ByteTrack, DeepSORT, etc.).
    """

    @abstractmethod
    def track(
        self,
        frame: np.ndarray,
        frame_index: int = 0,
        timestamp_seconds: float = 0.0,
    ) -> List[DetectionResult]:
        """
        Process a single video frame, associating detections with persistent track IDs.

        Args:
            frame: OpenCV image array (H, W, C) in BGR format.
            frame_index: Sequential index of the frame in the video stream.
            timestamp_seconds: Exact timestamp of the frame in seconds.

        Returns:
            List of DetectionResult objects with track_id populated when successfully tracked.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset internal tracking state and identity counters.
        Must be called between analysis jobs to guarantee strict isolation.
        """
        pass
