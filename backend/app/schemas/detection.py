from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box pixel coordinates relative to the processed frame resolution."""
    x1: int = Field(..., description="Top-left X coordinate")
    y1: int = Field(..., description="Top-left Y coordinate")
    x2: int = Field(..., description="Bottom-right X coordinate")
    y2: int = Field(..., description="Bottom-right Y coordinate")
    width: int = Field(..., description="Bounding box width")
    height: int = Field(..., description="Bounding box height")


class DetectionResponse(BaseModel):
    """Individual object detection response representation."""
    id: str
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None

    model_config = {"from_attributes": True}


class FrameDetectionResponse(BaseModel):
    """List of detections for a specific frame."""
    frame_id: str
    frame_index: int
    timestamp_seconds: float
    detection_count: int
    detections: List[DetectionResponse]


class DetectionSummary(BaseModel):
    """Aggregated detection analytics across all sampled frames of an analysis job."""
    total_detections: int
    frames_with_detections: int
    unique_classes: int
    average_confidence: float
    class_counts: Dict[str, int]
