import logging
from typing import Any, Dict, List, Optional

from app.models.security_rule import SecurityEventType
from app.vision.events.base import EventCandidate, SecurityEventDetector
from app.vision.events.geometry import normalize_point, point_in_polygon
from app.vision.events.rules import RuleDefinition

logger = logging.getLogger("sentinel.vision.events.crowd")


class CrowdDetector(SecurityEventDetector):
    """
    Detects when the number of tracked objects simultaneously present in a configured
    crowd zone meets or exceeds a configured threshold (e.g. >= 5 persons).
    Maintains continuous crowd event lifecycle, recording peak count and duration
    without flooding duplicate events per frame.
    """

    def __init__(self, rules: List[RuleDefinition]):
        self.rules = [
            r for r in rules
            if r.event_type == SecurityEventType.CROWD_DENSITY and r.zone_coordinates
        ]
        # rule_id -> active crowd session:
        # { "start_ts": float, "last_seen_ts": float, "peak_count": int,
        #   "evidence_id": str, "candidate": EventCandidate }
        self._active_crowd_events: Dict[str, dict] = {}

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
            crowd_threshold = int(rule.threshold_value) if rule.threshold_value is not None else 5
            inside_tracks = []

            for track in tracks:
                class_name = track["class_name"]
                conf = track.get("confidence", 1.0)

                # Default crowd tracking focuses on 'person' or rule's class filter
                if not rule.matches_class(class_name) or conf < rule.minimum_confidence:
                    continue

                cx = track["center_x"]
                cy = track["center_y"]
                norm_pt = normalize_point(cx, cy, frame_width, frame_height)

                if point_in_polygon(norm_pt, rule.zone_coordinates):
                    inside_tracks.append(track)

            count = len(inside_tracks)
            rule_id = rule.id

            if count >= crowd_threshold:
                zone_label = rule.zone_name or "Crowd Zone"

                if rule_id not in self._active_crowd_events:
                    # Initial crowd threshold crossing
                    title = "High Crowd Density Detected"
                    description = (
                        f"{count} tracked objects detected inside {zone_label}, "
                        f"exceeding threshold of {crowd_threshold}."
                    )
                    cand = EventCandidate(
                        rule_id=rule.id,
                        event_type=SecurityEventType.CROWD_DENSITY,
                        severity=rule.severity,
                        title=title,
                        description=description,
                        start_timestamp=round(timestamp_seconds, 2),
                        end_timestamp=round(timestamp_seconds, 2),
                        duration_seconds=0.0,
                        confidence=None,
                        track_id=None,
                        class_name="person",
                        evidence_frame_id=result_id,
                        metadata={
                            "zone_id": rule.zone_id,
                            "zone_name": rule.zone_name,
                            "threshold": crowd_threshold,
                            "peak_count": count,
                            "current_count": count,
                        },
                        is_active=True,
                        dedup_key=f"crowd:{rule_id}",
                    )
                    self._active_crowd_events[rule_id] = {
                        "start_ts": timestamp_seconds,
                        "last_seen_ts": timestamp_seconds,
                        "peak_count": count,
                        "candidate": cand,
                    }
                    candidates.append(cand)
                else:
                    # Update active crowd event with new duration and peak count
                    sess = self._active_crowd_events[rule_id]
                    sess["last_seen_ts"] = timestamp_seconds
                    if count > sess["peak_count"]:
                        sess["peak_count"] = count

                    duration = sess["last_seen_ts"] - sess["start_ts"]
                    cand = sess["candidate"]
                    cand.end_timestamp = round(timestamp_seconds, 2)
                    cand.duration_seconds = round(duration, 2)
                    cand.metadata["peak_count"] = sess["peak_count"]
                    cand.metadata["current_count"] = count
                    cand.description = (
                        f"Crowd of up to {sess['peak_count']} tracked objects inside {zone_label} "
                        f"(current: {count}, threshold: {crowd_threshold})."
                    )
            else:
                # Crowd dissipated below threshold
                if rule_id in self._active_crowd_events:
                    cand = self._active_crowd_events[rule_id]["candidate"]
                    cand.is_active = False
                    del self._active_crowd_events[rule_id]

        return candidates

    def finalize(self, final_timestamp: float) -> List[EventCandidate]:
        finalized: List[EventCandidate] = []
        for rule_id, sess in self._active_crowd_events.items():
            cand = sess["candidate"]
            cand.is_active = False
            finalized.append(cand)
        self._active_crowd_events.clear()
        return finalized
