from typing import Dict, List, Tuple

import cv2
import numpy as np

from app.vision.detection.detector import DetectionResult

# Curated BGR color palette matching the Dark SOC aesthetic
# Format: (Blue, Green, Red)
CLASS_COLOR_PALETTE: Dict[str, Tuple[int, int, int]] = {
    # Persons / Threats: Electric Cyan
    "person": (235, 175, 50),
    # Vehicles: Dynamic Amber / Tangerine
    "car": (45, 165, 245),
    "motorcycle": (45, 165, 245),
    "bus": (30, 140, 255),
    "truck": (30, 140, 255),
    "bicycle": (55, 195, 240),
    # Default fallback: Vibrant Emerald Green
    "default": (90, 215, 65),
}


def get_class_color(class_name: str) -> Tuple[int, int, int]:
    """Retrieve color tuple for a given class name."""
    return CLASS_COLOR_PALETTE.get(class_name.lower(), CLASS_COLOR_PALETTE["default"])


def annotate_frame(
    frame: np.ndarray,
    detections: List[DetectionResult],
    trajectories: Optional[Dict[int, List[Tuple[float, float]]]] = None,
    box_thickness: int = 2,
    font_scale: float = 0.5,
) -> np.ndarray:
    """
    Draw professional surveillance bounding boxes, label badges, and optional trajectory
    trails onto a frame. Returns a newly allocated copy without modifying original.

    Args:
        frame: Original image matrix (BGR).
        detections: List of DetectionResult objects to annotate.
        trajectories: Optional dict mapping track_id to list of (center_x, center_y) historical points.
        box_thickness: Border width of bounding box.
        font_scale: Text font scale.

    Returns:
        Annotated BGR image matrix.
    """
    if frame is None:
        return frame

    annotated = frame.copy()

    # 1. Render trajectory trails if provided
    if trajectories:
        for track_id, points in trajectories.items():
            if len(points) >= 2:
                # Find matching detection class for color coherence
                track_class = "default"
                for d in detections:
                    if d.track_id == track_id:
                        track_class = d.class_name
                        break
                trail_color = get_class_color(track_class)

                for i in range(len(points) - 1):
                    pt1 = (int(round(points[i][0])), int(round(points[i][1])))
                    pt2 = (int(round(points[i + 1][0])), int(round(points[i + 1][1])))
                    cv2.line(annotated, pt1, pt2, trail_color, 1, lineType=cv2.LINE_AA)
                    cv2.circle(annotated, pt1, 2, trail_color, -1, lineType=cv2.LINE_AA)
                pt_last = (int(round(points[-1][0])), int(round(points[-1][1])))
                cv2.circle(annotated, pt_last, 3, trail_color, -1, lineType=cv2.LINE_AA)

    # 2. Render bounding boxes and ID badges
    for det in detections:
        bbox = det.bbox
        x1, y1, x2, y2 = bbox.x1, bbox.y1, bbox.x2, bbox.y2
        color = get_class_color(det.class_name)

        # 1. Draw solid bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, box_thickness, lineType=cv2.LINE_AA)

        # 2. Format label string: e.g. "PERSON #7 94%" or "PERSON 94%"
        conf_pct = int(round(det.confidence * 100))
        if det.track_id is not None:
            label = f"{det.class_name.upper()} #{det.track_id} {conf_pct}%"
        else:
            label = f"{det.class_name.upper()} {conf_pct}%"

        # 3. Calculate text size for badge background
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, 1)

        # Label position: above box if space permits, otherwise inside
        badge_y2 = y1 if y1 - text_h - 8 >= 0 else y1 + text_h + 8
        badge_y1 = badge_y2 - text_h - 6
        badge_x1 = x1
        badge_x2 = x1 + text_w + 10

        # Draw filled label badge background
        cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), color, -1)

        # Draw dark contrast text inside badge
        text_origin = (badge_x1 + 5, badge_y2 - 4)
        cv2.putText(
            annotated,
            label,
            text_origin,
            font,
            font_scale,
            (15, 20, 28),  # Dark SOC charcoal text color for high contrast
            thickness=1,
            lineType=cv2.LINE_AA,
        )

    return annotated
