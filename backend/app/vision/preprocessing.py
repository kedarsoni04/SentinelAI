
import cv2
import numpy as np


def resize_frame(frame: np.ndarray, max_width: int = 1280) -> np.ndarray:
    """
    Resize a frame to a maximum width while strictly preserving aspect ratio.
    If the frame is already within max_width, returns original frame.
    """
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame

    scaling_factor = max_width / float(width)
    new_width = max_width
    new_height = int(round(height * scaling_factor))

    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)


def create_thumbnail(frame: np.ndarray, width: int = 320) -> np.ndarray:
    """
    Generate a lightweight thumbnail image for frontend gallery views.
    Preserves aspect ratio.
    """
    height, orig_width = frame.shape[:2]
    if orig_width <= width:
        return frame

    scaling_factor = width / float(orig_width)
    new_height = int(round(height * scaling_factor))

    return cv2.resize(frame, (width, new_height), interpolation=cv2.INTER_AREA)


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    """
    Convert OpenCV's default BGR color representation to RGB.
    Essential for future PyTorch / YOLO model inputs.
    """
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    """
    Convert image pixel intensities from [0, 255] uint8 to [0.0, 1.0] float32.
    """
    return frame.astype(np.float32) / 255.0
