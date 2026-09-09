from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.security_rule import SecurityEventSeverity, SecurityEventType
from app.models.security_zone import ZoneType


# ─── Security Zone Schemas ───────────────────────────────────────────────────

class CoordinatePoint(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Normalized X coordinate (0.0 to 1.0)")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized Y coordinate (0.0 to 1.0)")


class SecurityZoneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    camera_id: Optional[str] = None
    zone_type: ZoneType = ZoneType.RESTRICTED
    coordinates: List[CoordinatePoint] = Field(..., min_length=3)
    is_enabled: bool = True


class SecurityZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    camera_id: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    coordinates: Optional[List[CoordinatePoint]] = Field(None, min_length=3)
    is_enabled: Optional[bool] = None


class SecurityZoneResponse(BaseModel):
    id: str
    user_id: str
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    zone_type: ZoneType
    coordinates: List[Dict[str, float]]
    is_enabled: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ─── Security Rule Schemas ───────────────────────────────────────────────────

class SecurityRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    event_type: SecurityEventType
    severity: SecurityEventSeverity = SecurityEventSeverity.MEDIUM
    camera_id: Optional[str] = None
    zone_id: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_seconds: Optional[float] = None
    minimum_confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    class_filters: Optional[List[str]] = None
    is_enabled: bool = True


class SecurityRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    severity: Optional[SecurityEventSeverity] = None
    camera_id: Optional[str] = None
    zone_id: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_seconds: Optional[float] = None
    minimum_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    class_filters: Optional[List[str]] = None
    is_enabled: Optional[bool] = None


class SecurityRuleResponse(BaseModel):
    id: str
    user_id: str
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    is_enabled: bool
    threshold_value: Optional[float] = None
    threshold_seconds: Optional[float] = None
    minimum_confidence: Optional[float] = 0.5
    class_filters: Optional[List[str]] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ─── Security Event Schemas ──────────────────────────────────────────────────

class SecurityEventStatusUpdate(BaseModel):
    status: str = Field(..., description="Target status: OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED")


class SecurityEventResponse(BaseModel):
    id: str
    analysis_job_id: str
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    tracked_object_id: Optional[str] = None
    track_id: Optional[int] = None
    class_name: Optional[str] = None
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    status: str
    title: str
    description: str
    start_timestamp: float
    end_timestamp: Optional[float] = None
    duration_seconds: Optional[float] = None
    confidence: Optional[float] = None
    evidence_frame_id: Optional[str] = None
    evidence_frame_url: Optional[str] = None
    annotated_frame_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class EventMetricsResponse(BaseModel):
    total_events: int
    open_events: int
    high_severity_events: int
    medium_severity_events: int
    low_severity_events: int
    events_today: int
    by_type: Dict[str, int]

    model_config = {"from_attributes": True}
