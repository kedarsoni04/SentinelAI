import logging
from typing import Any, Dict, List, Optional

from app.vision.events.base import EventCandidate, SecurityEventDetector
from app.vision.events.crowd import CrowdDetector
from app.vision.events.intrusion import RestrictedZoneDetector
from app.vision.events.loitering import LoiteringDetector
from app.vision.events.movement import UnusualMovementDetector
from app.vision.events.rules import RuleDefinition
from app.vision.events.stationary import StationaryObjectDetector

logger = logging.getLogger("sentinel.vision.events.engine")


class EventEngine:
    """
    Centralized Security Event Engine.
    Instantiated per analysis job to maintain clean, isolated state.
    Coordinates all modular detectors (Intrusion, Loitering, Stationary, Crowd, Movement),
    accumulates emitted events, handles deduplication, and finalizes active events at video end.
    """

    def __init__(self, rules: List[RuleDefinition]):
        self.rules = rules
        self.detectors: List[SecurityEventDetector] = [
            RestrictedZoneDetector(rules),
            LoiteringDetector(rules),
            StationaryObjectDetector(rules),
            CrowdDetector(rules),
            UnusualMovementDetector(rules),
        ]
        # dedup_key -> EventCandidate
        self._persisted_events: Dict[str, EventCandidate] = {}

    def process_frame(
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
        Evaluate all enabled rules across all modular detectors for a single frame.
        Updates continuous events and returns newly emitted or updated candidates.
        """
        new_or_updated: List[EventCandidate] = []

        for detector in self.detectors:
            try:
                candidates = detector.evaluate(
                    frame_index=frame_index,
                    timestamp_seconds=timestamp_seconds,
                    result_id=result_id,
                    tracks=tracks,
                    trajectory_history=trajectory_history,
                    frame_width=frame_width,
                    frame_height=frame_height,
                )
                for cand in candidates:
                    self._persisted_events[cand.dedup_key] = cand
                    new_or_updated.append(cand)
            except Exception as e:
                logger.error(
                    f"Detector {detector.__class__.__name__} failed on frame {frame_index} "
                    f"at {timestamp_seconds:.1f}s: {e}",
                    exc_info=True,
                )

        return new_or_updated

    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        """
        Finalize all active detectors and return complete set of unique security events.
        """
        for detector in self.detectors:
            try:
                final_candidates = detector.finalize(final_timestamp)
                for cand in final_candidates:
                    self._persisted_events[cand.dedup_key] = cand
            except Exception as e:
                logger.error(f"Detector {detector.__class__.__name__} finalize failed: {e}")

        all_events = list(self._persisted_events.values())
        # Sort chronologically by start_timestamp
        all_events.sort(key=lambda ev: ev.start_timestamp)
        logger.info(f"EventEngine finalized {len(all_events)} security events.")
        return all_events
