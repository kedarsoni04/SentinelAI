import logging
from typing import Any, Dict, List, Set

from app.models.security_rule import SecurityEventType
from app.vision.events.base import EventCandidate, SecurityEventDetector
from app.vision.events.rules import RuleDefinition
from app.vision.tracking.trajectory import calculate_displacement

logger = logging.getLogger("sentinel.vision.events.movement")


class UnusualMovementDetector(SecurityEventDetector):
    """
    Detects unusual movement speed based on trajectory displacement over time.
    Calculates image-space speed (pixels/second) across the recent observation window.
    Triggers an event if speed exceeds the rule's configured threshold (e.g. >= 250 px/s).
    """

    def __init__(self, rules: List[RuleDefinition]):
        self.rules = [
            r for r in rules
            if r.event_type == SecurityEventType.UNUSUAL_MOVEMENT
        ]
        # (rule_id, track_id) -> set of track_ids that already triggered to avoid spam
        self._triggered_tracks: Set[str] = set()

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
            # Default speed threshold: 250 px/second
            speed_threshold = rule.threshold_value if rule.threshold_value is not None else 250.0

            for track in tracks:
                track_id = track["track_id"]
                class_name = track["class_name"]
                conf = track.get("confidence", 1.0)

                if not rule.matches_class(class_name) or conf < rule.minimum_confidence:
                    continue

                state_key = f"{rule.id}:{track_id}"
                if state_key in self._triggered_tracks:
                    continue

                history = trajectory_history.get(track_id, [])
                if len(history) < 2:
                    continue

                # Use the recent window (last 3-5 observations) to compute instantaneous speed
                recent_points = history[-4:]
                p_start = recent_points[0]
                p_end = recent_points[-1]
                dt = p_end["timestamp_seconds"] - p_start["timestamp_seconds"]

                if dt >= 0.2:  # Avoid division by very tiny intervals
                    dist = calculate_displacement(
                        (p_start["center_x"], p_start["center_y"]),
                        (p_end["center_x"], p_end["center_y"]),
                    )
                    speed_px_per_sec = dist / dt

                    if speed_px_per_sec >= speed_threshold:
                        title = "Unusual Movement Detected"
                        description = (
                            f"Tracked {class_name} #{track_id} exhibited high image-space speed of "
                            f"{speed_px_per_sec:.1f} px/s (configured threshold: {speed_threshold:.1f} px/s)."
                        )
                        candidates.append(
                            EventCandidate(
                                rule_id=rule.id,
                                event_type=SecurityEventType.UNUSUAL_MOVEMENT,
                                severity=rule.severity,
                                title=title,
                                description=description,
                                start_timestamp=round(p_start["timestamp_seconds"], 2),
                                end_timestamp=round(p_end["timestamp_seconds"], 2),
                                duration_seconds=round(dt, 2),
                                confidence=round(conf, 4),
                                track_id=track_id,
                                class_name=class_name,
                                evidence_frame_id=result_id,
                                metadata={
                                    "speed_threshold_px_s": speed_threshold,
                                    "observed_speed_px_s": round(speed_px_per_sec, 2),
                                    "displacement_pixels": round(dist, 2),
                                    "measurement_interval_seconds": round(dt, 2),
                                },
                                is_active=False,
                                dedup_key=state_key,
                            )
                        )
                        self._triggered_tracks.add(state_key)

        return candidates

    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        return []
