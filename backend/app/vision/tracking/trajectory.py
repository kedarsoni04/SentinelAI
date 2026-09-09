import math
from typing import List, Optional, Tuple


def calculate_center(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """
    Calculate the center coordinate of a bounding box.

    Args:
        x1: Left horizontal coordinate.
        y1: Top vertical coordinate.
        x2: Right horizontal coordinate.
        y2: Bottom vertical coordinate.

    Returns:
        (center_x, center_y) as floating-point pixel coordinates.
    """
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def calculate_displacement(
    start_point: Tuple[float, float],
    end_point: Tuple[float, float],
) -> float:
    """
    Calculate the net image-space displacement (Euclidean distance)
    between the first observed position and the last observed position.

    Formula: sqrt((x_end - x_start)^2 + (y_end - y_start)^2)

    Args:
        start_point: (x, y) coordinates of initial observation.
        end_point: (x, y) coordinates of final observation.

    Returns:
        Net displacement in pixels.
    """
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    return float(math.sqrt(dx * dx + dy * dy))


def calculate_trajectory_distance(points: List[Tuple[float, float]]) -> float:
    """
    Calculate cumulative image-space trajectory distance across all sequential observations.

    Formula: sum(sqrt((x_{i+1} - x_i)^2 + (y_{i+1} - y_i)^2)) for i in 0..N-1

    Args:
        points: Chronologically ordered list of (center_x, center_y) coordinates.

    Returns:
        Cumulative trajectory distance in pixels.
    """
    if len(points) < 2:
        return 0.0

    total_distance = 0.0
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        total_distance += math.sqrt(dx * dx + dy * dy)

    return float(total_distance)


def calculate_average_movement(points: List[Tuple[float, float]]) -> float:
    """
    Calculate average movement (in pixels) per consecutive observation step.

    Args:
        points: Chronologically ordered list of (center_x, center_y) coordinates.

    Returns:
        Average step distance in pixels, or 0.0 if fewer than 2 points.
    """
    if len(points) < 2:
        return 0.0
    dist = calculate_trajectory_distance(points)
    step_count = len(points) - 1
    return float(dist / step_count) if step_count > 0 else 0.0


def normalize_coordinate(val: float, dimension: float) -> float:
    """
    Safely normalize a pixel coordinate value against frame dimensions (0.0 to 1.0).
    """
    if dimension <= 0:
        return 0.0
    return float(max(0.0, min(1.0, val / dimension)))
