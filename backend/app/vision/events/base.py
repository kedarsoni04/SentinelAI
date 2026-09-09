from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.models.security_rule import SecurityEventSeverity, SecurityEventType


@dataclass
class EventCandidate:
    """
    Structured in-memory candidate representation emitted when an observable condition triggers.
    Can be instantaneous or continuous (with ongoing duration updates).
    """
    rule_id: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    title: str
    description: str
    start_timestamp: float
    end_timestamp: Optional[float] = None
    duration_seconds: Optional[float] = None
    confidence: Optional[float] = None
    tracked_object_id: Optional[str] = None
    track_id: Optional[int] = None
    class_name: Optional[str] = None
    evidence_frame_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = False
    dedup_key: str = ""  # Unique key for state tracking & debouncing


class SecurityEventDetector(ABC):
    """
    Abstract Base Class for modular, deterministic security event detectors.
    Every detector processes incoming frame observations, applies rule parameters,
    and returns detected event candidates.
    """

    @abstractmethod
    def evaluate(
        self,
        frame_index: int,
        timestamp_seconds: float,
        result_id: str,
        tracks: List[Dict[str, Any]],
        trajectory_history: Dict[int, List[Dict[str, Any]]],
        frame_width: int,
        frame_height: int,
    ) -> List[EventCandidate]:
        """
        Evaluate conditions for a single frame.

        Args:
            frame_index: Sequential index of sampled frame.
            timestamp_seconds: Video timeline timestamp in seconds.
            result_id: Database ID of the AnalysisResult (evidence frame).
            tracks: Current frame active detections with track_id, class, bbox, center.
            trajectory_history: Full track history per track_id up to current frame.
            frame_width: Frame pixel width.
            frame_height: Frame pixel height.

        Returns:
            List of newly triggered or updated EventCandidate objects.
        """
        pass

    @abstractmethod
    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        """
        Finalize any active ongoing conditions at analysis completion.

        Args:
            final_timestamp: The ending timestamp of the video.

        Returns:
            List of finalized EventCandidate objects ready for persistence.
        """
        pass
