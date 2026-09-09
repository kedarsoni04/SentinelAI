import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

from app.core.config import settings
from app.vision.detection.detector import DetectionResult, ObjectDetector
from app.vision.frame_extractor import ExtractedFrameInfo, save_frame_and_thumbnail
from app.vision.frame_sampler import FrameSampler
from app.vision.tracking.tracker import ObjectTracker
from app.vision.tracking.trajectory import calculate_center
from app.vision.video_reader import VideoMetadata, VideoReader

logger = logging.getLogger("sentinel.vision.analyzer")


class VideoAnalyzer:
    """
    Coordinates the video ingestion, OpenCV decoding, frame sampling,
    preprocessing, YOLO detection, object tracking, trajectory management,
    annotated frame generation, and storage pipeline.
    """

    def __init__(
        self,
        video_path: str,
        output_dir: str,
        interval_seconds: float = 2.0,
        max_frame_width: int = 1280,
        thumbnail_width: int = 320,
        detector: Optional[ObjectDetector] = None,
        tracker: Optional[ObjectTracker] = None,
        annotated_dir: Optional[str] = None,
    ):
        self.video_path = video_path
        self.output_dir = output_dir
        self.interval_seconds = interval_seconds
        self.max_frame_width = max_frame_width
        self.thumbnail_width = thumbnail_width
        self.detector = detector
        self.tracker = tracker
        self.annotated_dir = annotated_dir

    def run(
        self,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
        is_cancelled_callback: Optional[Callable[[], bool]] = None,
    ) -> Tuple[VideoMetadata, List[ExtractedFrameInfo]]:
        """
        Execute the full analysis pipeline (detection + tracking + annotation).

        Frames are processed in strict chronological order to maintain tracker
        state continuity. Trajectory history per track_id is maintained in-memory
        and trimmed to TRACK_MAX_TRAJECTORY_POINTS for frame annotation.

        Args:
            progress_callback: Optional callback func(processed_frames, total_sampled, percent)
            is_cancelled_callback: Optional callback returning True if cancellation requested

        Returns:
            Tuple of (VideoMetadata, List of ExtractedFrameInfo)
        """
        logger.info(f"Starting video analysis on {self.video_path}")

        # Per-job trajectory buffer: track_id -> list[(center_x, center_y)] chronological
        trajectory_buffer: Dict[int, List[Tuple[float, float]]] = defaultdict(list)
        max_traj_points = settings.TRACK_MAX_TRAJECTORY_POINTS
        draw_trajectory = settings.TRACK_DRAW_TRAJECTORY

        with VideoReader(self.video_path) as reader:
            metadata = reader.metadata
            sampler = FrameSampler(
                fps=metadata.fps,
                total_frames=metadata.frame_count,
                interval_seconds=self.interval_seconds,
            )

            results: List[ExtractedFrameInfo] = []
            planned_count = max(1, sampler.planned_count)
            processed_count = 0

            # Iterate frames strictly sequentially — never loading entire video into memory
            for frame_index, frame in reader.iter_frames():
                if is_cancelled_callback and is_cancelled_callback():
                    logger.warning(f"Video analysis cancelled for {self.video_path}")
                    break

                if sampler.should_sample(frame_index):
                    timestamp = sampler.timestamp_for_frame(frame_index)

                    # Update trajectory buffer from previous frame detections before calling save
                    # (trajectories passed here are the *current accumulated history*)
                    traj_for_annotation = None
                    if draw_trajectory and self.tracker is not None:
                        traj_for_annotation = {
                            tid: list(pts[-max_traj_points:])
                            for tid, pts in trajectory_buffer.items()
                            if pts
                        }

                    frame_info = save_frame_and_thumbnail(
                        frame=frame,
                        output_dir=self.output_dir,
                        frame_index=frame_index,
                        timestamp_seconds=timestamp,
                        max_frame_width=self.max_frame_width,
                        thumbnail_width=self.thumbnail_width,
                        detector=self.detector,
                        tracker=self.tracker,
                        annotated_dir=self.annotated_dir,
                        trajectories=traj_for_annotation,
                    )

                    # After getting detections back, update trajectory buffers
                    if self.tracker is not None:
                        for det in frame_info.detections:
                            if det.track_id is not None:
                                cx, cy = calculate_center(
                                    det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2
                                )
                                trajectory_buffer[det.track_id].append((cx, cy))
                                # Trim buffer to avoid unbounded memory growth
                                if len(trajectory_buffer[det.track_id]) > max_traj_points * 2:
                                    trajectory_buffer[det.track_id] = trajectory_buffer[det.track_id][-max_traj_points:]

                    results.append(frame_info)
                    processed_count += 1

                    if progress_callback:
                        pct = int(min(99, round((processed_count / planned_count) * 100)))
                        progress_callback(processed_count, planned_count, pct)

            logger.info(
                f"Analysis completed for {self.video_path}: "
                f"sampled {len(results)} frames, "
                f"tracked {len(trajectory_buffer)} unique object IDs"
            )
            return metadata, results
