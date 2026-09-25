import os
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.vision.detection.annotation import annotate_frame
from app.vision.detection.detector import DetectionResult, ObjectDetector
from app.vision.preprocessing import create_thumbnail, resize_frame
from app.vision.tracking.tracker import ObjectTracker


@dataclass
class ExtractedFrameInfo:
    """Metadata for a saved sampled frame, including optional AI object detections."""
    frame_index: int
    timestamp_seconds: float
    frame_path: str
    thumbnail_path: str
    width: int
    height: int
    processing_time_ms: float
    annotated_frame_path: Optional[str] = None
    detections: List[DetectionResult] = field(default_factory=list)
    detection_time_ms: float = 0.0


def save_frame_and_thumbnail(
    frame: np.ndarray,
    output_dir: str,
    frame_index: int,
    timestamp_seconds: float,
    max_frame_width: int = 1280,
    thumbnail_width: int = 320,
    jpeg_quality: int = 85,
    detector: Optional[ObjectDetector] = None,
    tracker: Optional[ObjectTracker] = None,
    annotated_dir: Optional[str] = None,
    trajectories: Optional[dict] = None,
) -> ExtractedFrameInfo:
    """
    Apply preprocessing, optionally run object detection / tracking, save the full frame,
    thumbnail, and annotated frame, and measure frame processing latency.
    """
    t0 = time.perf_counter()

    os.makedirs(output_dir, exist_ok=True)
    if annotated_dir:
        os.makedirs(annotated_dir, exist_ok=True)

    # 1. Resize main frame if necessary
    processed_frame = resize_frame(frame, max_width=max_frame_width)
    height, width = processed_frame.shape[:2]

    # 2. Run Object Tracking or Detection
    detections: List[DetectionResult] = []
    det_elapsed_ms = 0.0
    annotated_path: Optional[str] = None

    if tracker is not None:
        t_det = time.perf_counter()
        detections = tracker.track(processed_frame, frame_index, timestamp_seconds)
        det_elapsed_ms = round((time.perf_counter() - t_det) * 1000.0, 2)
    elif detector is not None:
        t_det = time.perf_counter()
        detections = detector.detect(processed_frame)
        det_elapsed_ms = round((time.perf_counter() - t_det) * 1000.0, 2)

    # 3. Format file names
    frame_filename = f"frame_{frame_index:06d}.jpg"
    thumb_filename = f"thumb_{frame_index:06d}.jpg"
    frame_path = os.path.join(output_dir, frame_filename)
    thumb_path = os.path.join(output_dir, thumb_filename)

    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]

    # 4. Generate & save annotated frame if annotated_dir is configured
    if annotated_dir:
        annotated_filename = f"annotated_{frame_index:06d}.jpg"
        annotated_path = os.path.join(annotated_dir, annotated_filename)
        annotated_img = annotate_frame(processed_frame, detections, trajectories=trajectories)
        cv2.imwrite(annotated_path, annotated_img, encode_params)

    # 5. Generate thumbnail (from processed_frame)
    thumb = create_thumbnail(processed_frame, width=thumbnail_width)

    # 6. Save original representative frame and thumbnail
    cv2.imwrite(frame_path, processed_frame, encode_params)
    cv2.imwrite(thumb_path, thumb, encode_params)

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return ExtractedFrameInfo(
        frame_index=frame_index,
        timestamp_seconds=timestamp_seconds,
        frame_path=frame_path,
        thumbnail_path=thumb_path,
        width=width,
        height=height,
        processing_time_ms=elapsed_ms,
        annotated_frame_path=annotated_path,
        detections=detections,
        detection_time_ms=det_elapsed_ms,
    )
