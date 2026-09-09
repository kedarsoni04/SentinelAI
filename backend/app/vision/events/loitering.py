import logging
from typing import Any, Dict, List, Optional

from app.models.security_rule import SecurityEventType
from app.vision.events.base import EventCandidate, SecurityEventDetector
from app.vision.events.geometry import normalize_point, point_in_polygon
from app.vision.events.rules import RuleDefinition

logger = logging.getLogger("sentinel.vision.events.loitering")


class LoiteringDetector(SecurityEventDetector):
    """
    Detects when a tracked object remains within a configured security zone for
    longer than a configured time threshold (e.g. >= 15 seconds).
    Maintains ongoing loitering session state per track, debouncing updates and
    finalizing when the object exits the zone or analysis completes.
    """

    def __init__(self, rules: List[RuleDefinition]):
        self.rules = [
            r for r in rules
            if r.event_type == SecurityEventType.LOITERING and r.zone_coordinates
        ]
        # state_key -> session dict:
        # { "rule": rule, "entry_ts": float, "last_seen_ts": float, "evidence_id": str,
        #   "triggered": bool, "track_id": int, "class_name": str, "confidences": list[float] }
        self._active_sessions: Dict[str, dict] = {}
        # Emitted candidates that have triggered but are still updating duration
        self._emitted_candidates: Dict[str, EventCandidate] = {}

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
        currently_inside_keys = set()

        for rule in self.rules:
            threshold_sec = rule.threshold_seconds or 10.0

            for track in tracks:
                track_id = track["track_id"]
                class_name = track["class_name"]
                conf = track.get("confidence", 1.0)

                if not rule.matches_class(class_name) or conf < rule.minimum_confidence:
                    continue

                cx = track["center_x"]
                cy = track["center_y"]
                norm_pt = normalize_point(cx, cy, frame_width, frame_height)

                state_key = f"{rule.id}:{track_id}"

                if point_in_polygon(norm_pt, rule.zone_coordinates):
                    currently_inside_keys.add(state_key)

                    if state_key not in self._active_sessions:
                        # First observation inside zone: begin session tracking
                        self._active_sessions[state_key] = {
                            "rule": rule,
                            "entry_ts": timestamp_seconds,
                            "last_seen_ts": timestamp_seconds,
                            "evidence_id": result_id,
                            "triggered": False,
                            "track_id": track_id,
                            "class_name": class_name,
                            "confidences": [conf],
                        }
                    else:
                        sess = self._active_sessions[state_key]
                        sess["last_seen_ts"] = timestamp_seconds
                        sess["confidences"].append(conf)

                        duration = sess["last_seen_ts"] - sess["entry_ts"]

                        # Check if threshold crossed
                        if duration >= threshold_sec:
                            avg_conf = sum(sess["confidences"]) / len(sess["confidences"])
                            zone_label = rule.zone_name or "Configured Zone"

                            if not sess["triggered"]:
                                # Initial trigger
                                sess["triggered"] = True
                                title = "Potential Loitering Detected"
                                description = (
                                    f"Tracked {class_name} #{track_id} remained inside {zone_label} "
                                    f"for {duration:.1f}s (configured threshold: {threshold_sec:.1f}s)."
                                )
                                cand = EventCandidate(
                                    rule_id=rule.id,
                                    event_type=SecurityEventType.LOITERING,
                                    severity=rule.severity,
                                    title=title,
                                    description=description,
                                    start_timestamp=round(sess["entry_ts"], 2),
                                    end_timestamp=round(timestamp_seconds, 2),
                                    duration_seconds=round(duration, 2),
                                    confidence=round(avg_conf, 4),
                                    track_id=track_id,
                                    class_name=class_name,
                                    evidence_frame_id=sess["evidence_id"],
                                    metadata={
                                        "zone_id": rule.zone_id,
                                        "zone_name": rule.zone_name,
                                        "threshold_seconds": threshold_sec,
                                        "observed_duration_seconds": round(duration, 2),
                                    },
                                    is_active=True,
                                    dedup_key=state_key,
                                )
                                self._emitted_candidates[state_key] = cand
                                candidates.append(cand)
                            else:
                                # Update duration for existing continuous loitering event
                                cand = self._emitted_candidates[state_key]
                                cand.end_timestamp = round(timestamp_seconds, 2)
                                cand.duration_seconds = round(duration, 2)
                                cand.description = (
                                    f"Tracked {class_name} #{track_id} remained inside {zone_label} "
                                    f"for {duration:.1f}s (configured threshold: {threshold_sec:.1f}s)."
                                )
                                cand.metadata["observed_duration_seconds"] = round(duration, 2)

        # Check for tracks that left the zone
        for key in list(self._active_sessions.keys()):
            if key not in currently_inside_keys:
                # Track exited the zone: finalize active candidate if triggered
                if key in self._emitted_candidates:
                    self._emitted_candidates[key].is_active = False
                    del self._emitted_candidates[key]
                del self._active_sessions[key]

        return candidates

    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        finalized: List[EventCandidate] = []
        for key, cand in self._emitted_candidates.items():
            cand.is_active = False
            finalized.append(cand)
        self._emitted_candidates.clear()
        self._active_sessions.clear()
        return finalized
