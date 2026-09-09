from typing import List, Set


class FrameSampler:
    """
    Intelligent frame sampling strategy.

    Selects representative frames at regular time intervals (e.g. every 2 seconds)
    rather than processing all 30/60 FPS, reducing CPU usage and storage.
    """

    def __init__(self, fps: float, total_frames: int, interval_seconds: float = 2.0):
        self.fps = fps if fps > 0 else 30.0
        self.total_frames = max(0, total_frames)
        self.interval_seconds = max(0.1, interval_seconds)

        # Compute interval in frames
        self.step = max(1, int(round(self.fps * self.interval_seconds)))

        # Pre-compute target frame indices
        if self.total_frames > 0:
            indices = list(range(0, self.total_frames, self.step))
            # Always ensure the first frame is included
            if not indices:
                indices = [0]
            self._target_indices: Set[int] = set(indices)
            self._ordered_indices: List[int] = indices
        else:
            self._target_indices = set()
            self._ordered_indices = []

    @property
    def target_indices(self) -> Set[int]:
        """Set of frame indices planned for sampling."""
        return self._target_indices

    @property
    def planned_count(self) -> int:
        """Total number of frames expected to be sampled."""
        return len(self._ordered_indices)

    def should_sample(self, frame_index: int) -> bool:
        """Return True if the given frame_index should be sampled."""
        if self._target_indices:
            return frame_index in self._target_indices
        # Fallback for streams/videos with unknown total_frames
        return (frame_index % self.step) == 0

    def timestamp_for_frame(self, frame_index: int) -> float:
        """Calculate video timestamp in seconds for a given frame index."""
        if self.fps > 0:
            return round(frame_index / self.fps, 3)
        return 0.0
