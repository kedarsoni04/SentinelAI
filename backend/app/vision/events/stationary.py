import logging
from typing import Any, Dict, List, Set

from app.models.security_rule import SecurityEventType
from app.vision.events.base import EventCandidate, SecurityEventDetector
from app.vision.events.rules import RuleDefinition
from app.vision.tracking.trajectory import calculate_displacement

logger = logging.getLogger("sentinel.vision.events.stationary")


class StationaryObjectDetector(SecurityEventDetector):
    """
    Detects when a tracked object remains approximately stationary
    (net displacement across its trajectory window <= movement_threshold_pixels)
    for a duration exceeding configured threshold_seconds (e.g. >= 15 seconds).
    """

    def __init__(self, rules: List[RuleDefinition]):
        self.rules = [
            r for r in rules
            if r.event_type == SecurityEventType.STATIONARY_OBJECT
        ]
        # (rule_id, track_id) -> already triggered event candidate
        self._triggered_events: Dict[str, EventCandidate] = {}
        # Set of keys already evaluated to avoid repeat triggers
        self._completed_keys: Set[str] = set()

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
        candidates: List[EventCandidate] = []

        for rule in self.rules:
            # Defaults: max 25 pixels movement to be considered stationary, min 15 seconds
            move_thresh_px = rule.threshold_value if rule.threshold_value is not None else 25.0
            dur_thresh_sec = rule.threshold_seconds if rule.threshold_seconds is not None else 15.0

            for track in tracks:
                track_id = track["track_id"]
                class_name = track["class_name"]
                conf = track.get("confidence", 1.0)

                if not rule.matches_class(class_name) or conf < rule.minimum_confidence:
                    continue

                state_key = f"{rule.id}:{track_id}"
                if state_key in self._completed_keys:
                    continue

                history = trajectory_history.get(track_id, [])
                if len(history) < 2:
                    continue

                first_obs = history[0]
                last_obs = history[-1]
                duration = last_obs["timestamp_seconds"] - first_obs["timestamp_seconds"]

                if duration >= dur_thresh_sec:
                    # Compute net displacement between initial and current position
                    p1 = (first_obs["center_x"], first_obs["center_y"])
                    p2 = (last_obs["center_x"], last_obs["center_y"])
                    displacement = calculate_displacement(p1, p2)

                    if displacement <= move_thresh_px:
                        if state_key not in self._triggered_events:
                            confidences = [pt.get("confidence", 1.0) for pt in history]
                            avg_conf = sum(confidences) / len(confidences)

                            title = "Stationary Object Detected"
                            description = (
                                f"Tracked {class_name} #{track_id} remained approximately stationary "
                                f"for {duration:.1f}s (displacement: {displacement:.1f}px <= {move_thresh_px:.1f}px threshold)."
                            )
                            cand = EventCandidate(
                                rule_id=rule.id,
                                event_type=SecurityEventType.STATIONARY_OBJECT,
                                severity=rule.severity,
                                title=title,
                                description=description,
                                start_timestamp=round(first_obs["timestamp_seconds"], 2),
                                end_timestamp=round(last_obs["timestamp_seconds"], 2),
                                duration_seconds=round(duration, 2),
                                confidence=round(avg_conf, 4),
                                track_id=track_id,
                                class_name=class_name,
                                evidence_frame_id=result_id,
                                metadata={
                                    "threshold_seconds": dur_thresh_sec,
                                    "movement_threshold_pixels": move_thresh_px,
                                    "observed_displacement_pixels": round(displacement, 2),
                                    "observed_duration_seconds": round(duration, 2),
                                },
                                is_active=True,
                                dedup_key=state_key,
                            )
                            self._triggered_events[state_key] = cand
                            candidates.append(cand)
                        else:
                            # Update duration for existing active stationary event
                            cand = self._triggered_events[state_key]
                            cand.end_timestamp = round(last_obs["timestamp_seconds"], 2)
                            cand.duration_seconds = round(duration, 2)
                            cand.metadata["observed_duration_seconds"] = round(duration, 2)
                            cand.metadata["observed_displacement_pixels"] = round(displacement, 2)
                    else:
                        # Movement exceeded threshold: object is moving, close if active
                        if state_key in self._triggered_events:
                            self._triggered_events[state_key].is_active = False
                            self._completed_keys.add(state_key)
                            del self._triggered_events[state_key]

        return candidates

    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        finalized: List[EventCandidate] = []
        for key, cand in self._triggered_events.items():
            cand.is_active = False
            finalized.append(cand)
        self._triggered_events.clear()
        return finalized
