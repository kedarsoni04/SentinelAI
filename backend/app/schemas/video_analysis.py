from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.analysis_job import JobStatus


# ─── Response Schemas ─────────────────────────────────────────────────────────


class AnalysisJobCreateResponse(BaseModel):
    """Initial response returned upon video upload."""

    id: str
    status: JobStatus
    original_filename: str
    progress: int = 0
    message: str = "Video uploaded successfully and queued for analysis."


class AnalysisJobResponse(BaseModel):
    """
    Public representation of a video analysis job.
    Never exposes internal server filesystem paths.
    """

    id: str
    user_id: str
    camera_id: Optional[str] = None
    source_type: str
    original_filename: str
    status: JobStatus
    progress: int
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

    active_jobs: int
    queued: int
    processing: int
