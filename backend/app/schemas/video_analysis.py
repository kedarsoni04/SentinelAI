from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.analysis_job import JobStatus
from app.schemas.camera import CameraResponse


# ─── Response Schemas ─────────────────────────────────────────────────────────


class AnalysisJobCreateResponse(BaseModel):
    """Initial response returned upon video upload."""

    id: str = Field(..., description="Unique analysis job UUID")
    status: JobStatus = Field(..., description="Initial job status (typically QUEUED)")
    original_filename: str = Field(..., description="Original uploaded filename")
    progress: int = Field(0, ge=0, le=100, description="Processing progress percentage (0-100)")
    message: str = Field(
        "Video uploaded successfully and queued for analysis.",
        description="User-friendly status confirmation message",
    )

    model_config = {"from_attributes": True}


class AnalysisJobResponse(BaseModel):
    """
    Public representation of a video analysis job.
    Never exposes internal server filesystem paths.
    """

    id: str
    user_id: str
    camera_id: Optional[str] = None
    source_type: str = "VIDEO_FILE"
    original_filename: str
    status: JobStatus
    progress: int = Field(0, ge=0, le=100)
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sampled_frames: int = 0
    processed_frames: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None
    camera: Optional[CameraResponse] = None

    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    """
    Public representation of an extracted sampled frame result.
    Uses safe, authenticated API URLs rather than local file paths.
    """

    id: str
    analysis_job_id: str
    frame_index: int
    timestamp_seconds: float
    frame_url: str
    thumbnail_url: Optional[str] = None
    annotated_frame_url: Optional[str] = None
    detection_count: int = 0
    width: int
    height: int
    processing_time_ms: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActiveJobsCountResponse(BaseModel):
    """Count of active analysis jobs for the SOC dashboard."""

    active_jobs: int = Field(..., ge=0, description="Total active (queued + processing) jobs")
    queued: int = Field(..., ge=0, description="Count of queued jobs")
    processing: int = Field(..., ge=0, description="Count of currently processing jobs")

    model_config = {"from_attributes": True}


__all__ = [
    "JobStatus",
    "AnalysisJobCreateResponse",
    "AnalysisJobResponse",
    "AnalysisResultResponse",
    "ActiveJobsCountResponse",
]
