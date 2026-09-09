import logging
from dataclasses import dataclass
from typing import Generator, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("sentinel.vision.video_reader")


@dataclass
class VideoMetadata:
    """Metadata extracted from a video source via OpenCV."""
    duration_seconds: float
    fps: float
    frame_count: int
    width: int
    height: int


class VideoReader:
    """
    Thread-safe abstraction around cv2.VideoCapture.

    Guarantees proper resource release on exit or exception.
    Extracts stream metadata safely and supports sequential frame iteration.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._cap: Optional[cv2.VideoCapture] = None
        self._metadata: Optional[VideoMetadata] = None

    def __enter__(self) -> "VideoReader":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self) -> None:
        """Open the video stream and validate decoding."""
        logger.info(f"Opening video file: {self.file_path}")
        self._cap = cv2.VideoCapture(self.file_path)

        if not self._cap.isOpened():
            logger.error(f"Failed to open video file: {self.file_path}")
            raise ValueError(
                "Unable to open or decode video file. Format may be unsupported or corrupted."
            )

        # Extract metadata
        fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        # Safe duration calculation
        if fps > 0 and frame_count > 0:
            duration = float(frame_count / fps)
        else:
            duration = 0.0

        self._metadata = VideoMetadata(
            duration_seconds=round(duration, 3),
            fps=round(fps, 2),
            frame_count=frame_count,
            width=width,
            height=height,
        )
        logger.info(
            f"Extracted metadata: {width}x{height} @ {fps}fps, "
            f"frames={frame_count}, duration={duration:.2f}s"
        )

    def close(self) -> None:
        """Release underlying OpenCV VideoCapture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.debug(f"Released video capture: {self.file_path}")

    @property
    def metadata(self) -> VideoMetadata:
        """Get the extracted metadata. Raises if video not opened."""
        if self._metadata is None:
            raise RuntimeError("VideoReader is not open. Call open() first.")
        return self._metadata

    def iter_frames(self) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Sequentially yield (frame_index, frame_ndarray) for all readable frames.
        Does not load the whole video into RAM.
        """
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("VideoReader is not open.")

        # Rewind to start
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_index = 0

        while True:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                break
            yield frame_index, frame
            frame_index += 1
