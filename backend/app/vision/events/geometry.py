"""
Geometry utilities for resolution-independent security zone evaluation.
Supports normalized coordinates (0.0 <= x, y <= 1.0) and ray-casting
point-in-polygon containment testing.
"""
from typing import Any, Dict, List, Tuple


def point_in_polygon(
    point: Tuple[float, float],
    polygon: List[Dict[str, float]],
) -> bool:
    """
    Determine if a 2D point (px, py) is inside a polygon using the standard ray-casting algorithm.
    The polygon is represented as a list of dicts: [{"x": float, "y": float}, ...]
    Works identically for normalized coordinates or pixel coordinates, as long as point
    and polygon are in the same coordinate space.

    Args:
        point: Tuple of (x, y) coordinates.
        polygon: List of vertices with "x" and "y" keys. Must contain at least 3 vertices.

    Returns:
        True if the point lies strictly inside or on the polygon boundary; False otherwise.
    """
    if len(polygon) < 3:
        return False

    px, py = point
    n = len(polygon)
    inside = False

    p1x = polygon[0]["x"]
    p1y = polygon[0]["y"]

    for i in range(1, n + 1):
        p2x = polygon[i % n]["x"]
        p2y = polygon[i % n]["y"]

        # Check if the ray horizontal to the right intersects the edge (p1, p2)
        if py > min(p1y, p2y):
            if py <= max(p1y, p2y):
                if px <= max(p1x, p2x):
                    if p1y != p2y:
                        x_inters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        x_inters = p1x

                    if p1x == p2x or px <= x_inters:
                        inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def normalize_point(
    x: float,
    y: float,
    frame_width: int,
    frame_height: int,
) -> Tuple[float, float]:
    """
    Convert absolute pixel coordinates to normalized [0.0, 1.0] coordinates.
    Guards against division by zero.
    """
    w = max(1, frame_width)
    h = max(1, frame_height)
    norm_x = max(0.0, min(1.0, x / w))
    norm_y = max(0.0, min(1.0, y / h))
    return (norm_x, norm_y)


def validate_polygon_coordinates(coordinates: Any) -> Tuple[bool, str]:
    """
    Validate that coordinates represent a valid polygon:
    - Must be a list of at least 3 points
    - Each item must have 'x' and 'y' numeric keys
    - Coordinates must be within normalized range [0.0, 1.0]

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(coordinates, list):
        return False, "Zone coordinates must be a list of points."

    if len(coordinates) < 3:
        return False, "A security zone polygon must contain at least 3 vertices."

    for idx, pt in enumerate(coordinates):
        if not isinstance(pt, dict) or "x" not in pt or "y" not in pt:
            return False, f"Vertex at index {idx} must be an object with 'x' and 'y' numbers."

        x, y = pt["x"], pt["y"]
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return False, f"Vertex at index {idx} contains non-numeric coordinates."

        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return False, f"Vertex at index {idx} ({x}, {y}) is outside normalized range [0.0, 1.0]."

    return True, ""
