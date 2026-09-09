from typing import List, Optional
from pydantic import BaseModel


class TrackPointResponse(BaseModel):
    frame_index: int
    timestamp_seconds: float
    center_x: float
    center_y: float
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float

    model_config = {"from_attributes": True}


class TrackedObjectResponse(BaseModel):
    id: str
    track_id: int
    class_id: int
    class_name: str
    first_seen_timestamp: float
    last_seen_timestamp: float
    duration_seconds: float
    first_seen_frame: int
    last_seen_frame: int
    total_frames: int
    average_confidence: float
    max_confidence: float

    model_config = {"from_attributes": True}


class TrackDetailResponse(BaseModel):
    id: str
    track_id: int
    class_id: int
    class_name: str
    first_seen_timestamp: float
    last_seen_timestamp: float
    duration_seconds: float
    first_seen_frame: int
    last_seen_frame: int
    total_frames: int
    average_confidence: float
    max_confidence: float
    displacement_pixels: float
    trajectory_distance_pixels: float
    trajectory: List[TrackPointResponse]

    model_config = {"from_attributes": True}


class TrackingSummaryResponse(BaseModel):
    total_tracked_objects: int
    tracked_persons: int
    tracked_vehicles: int
    longest_track_duration_seconds: float
    average_track_duration_seconds: float
    average_observations_per_track: float
    most_frequently_tracked_class: Optional[str]

    model_config = {"from_attributes": True}
