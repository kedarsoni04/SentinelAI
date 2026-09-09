"""
Pydantic schemas for the Incident Intelligence API (Phase 8).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── Request Schemas ──────────────────────────────────────────────────────────

class IncidentReportCreateRequest(BaseModel):
    """Request body for creating an AI incident report."""
    event_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of SecurityEvent IDs to include in the AI analysis (1–50).",
    )
    analysis_job_id: Optional[str] = Field(
        None,
        description="Optional AnalysisJob ID to pull additional video metadata from.",
    )


# ─── Response Schemas ─────────────────────────────────────────────────────────

class IncidentTimelineItem(BaseModel):
    """A single item in the AI-generated event timeline."""
    timestamp_label: str
    event_type: str
    description: str


class IncidentReportResponse(BaseModel):
    """Full AI incident report response."""
    id: str
    user_id: str
    analysis_job_id: Optional[str] = None
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    event_ids: List[str]
    event_count: int
    ai_provider: str
    ai_model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    summary: Optional[str] = None
    timeline: Optional[List[Dict[str, str]]] = None
    risk_level: Optional[str] = None
    risk_explanation: Optional[str] = None
    recommendations: Optional[List[str]] = None
    disclaimer: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class IncidentReportListItem(BaseModel):
    """Compact incident report representation for list views."""
    id: str
    user_id: str
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    event_count: int
    ai_provider: str
    risk_level: Optional[str] = None
    summary_preview: Optional[str] = None   # first 200 chars of summary
    status: str
    created_at: str

    model_config = {"from_attributes": True}
