import logging
from typing import Any, Dict, List, Set

from app.models.security_rule import SecurityEventType
from app.vision.events.base import EventCandidate, SecurityEventDetector
from app.vision.events.geometry import normalize_point, point_in_polygon
from app.vision.events.rules import RuleDefinition

logger = logging.getLogger("sentinel.vision.events.intrusion")


class RestrictedZoneDetector(SecurityEventDetector):
    """
    Detects when a tracked object enters a configured restricted zone.
    Maintains prior containment state per track to trigger an event ONLY upon boundary entry
    (transition from outside -> inside), preventing duplicate events while the object remains inside.
    """

    def __init__(self, rules: List[RuleDefinition]):
        self.rules = [
            r for r in rules
            if r.event_type == SecurityEventType.INTRUSION and r.zone_coordinates
        ]
        # (rule_id, track_id) -> whether track was inside zone on last observation
        self._inside_state: Dict[str, bool] = {}
        # (rule_id, track_id) -> set of track_ids that already triggered an intrusion
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
            for track in tracks:
                track_id = track["track_id"]
                class_name = track["class_name"]
                conf = track.get("confidence", 1.0)

                # Class filter & minimum confidence
                if not rule.matches_class(class_name) or conf < rule.minimum_confidence:
                    continue

                cx = track["center_x"]
                cy = track["center_y"]
                norm_pt = normalize_point(cx, cy, frame_width, frame_height)

                is_inside = point_in_polygon(norm_pt, rule.zone_coordinates)
                state_key = f"{rule.id}:{track_id}"
                was_inside = self._inside_state.get(state_key, False)

                # Boundary crossing check: outside -> inside
                if is_inside and not was_inside and state_key not in self._triggered_tracks:
                    zone_label = rule.zone_name or "Restricted Zone"
                    title = "Restricted Zone Intrusion"
                    description = (
                        f"Tracked {class_name} #{track_id} crossed boundary into {zone_label} "
                        f"at {timestamp_seconds:.1f}s."
                    )
                    candidates.append(
                        EventCandidate(
                            rule_id=rule.id,
                            event_type=SecurityEventType.INTRUSION,
                            severity=rule.severity,
                            title=title,
                            description=description,
                            start_timestamp=timestamp_seconds,
                            end_timestamp=timestamp_seconds,
                            duration_seconds=0.0,
                            confidence=round(conf, 4),
                            track_id=track_id,
                            class_name=class_name,
                            evidence_frame_id=result_id,
                            metadata={
                                "zone_id": rule.zone_id,
                                "zone_name": rule.zone_name,
                                "entry_point": {"x": round(norm_pt[0], 4), "y": round(norm_pt[1], 4)},
                                "frame_index": frame_index,
                            },
                            is_active=False,
                            dedup_key=state_key,
                        )
                    )
                    self._triggered_tracks.add(state_key)

                # Update current state
                self._inside_state[state_key] = is_inside

        return candidates

    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        # Intrusion is an instantaneous boundary crossing event, nothing pending
        return []
