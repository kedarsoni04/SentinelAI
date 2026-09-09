"""
Pydantic Schemas for SentinelAI Phase 9 — Advanced Analytics & Anomaly Intelligence.
All types are explicitly defined, strictly validated, and avoid 'Any'.
"""
import enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class DateRangePreset(str, enum.Enum):
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    CUSTOM = "custom"


class AnomalyType(str, enum.Enum):
    EVENT_VOLUME_SPIKE = "EVENT_VOLUME_SPIKE"
    SEVERITY_SPIKE = "SEVERITY_SPIKE"
    CAMERA_ACTIVITY_SPIKE = "CAMERA_ACTIVITY_SPIKE"
    UNUSUAL_TIME_ACTIVITY = "UNUSUAL_TIME_ACTIVITY"


class AnomalySeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InsightType(str, enum.Enum):
    TOP_CAMERA = "TOP_CAMERA"
    TOP_EVENT_TYPE = "TOP_EVENT_TYPE"
    PEAK_ACTIVITY_TIME = "PEAK_ACTIVITY_TIME"
    SEVERITY_TREND = "SEVERITY_TREND"
    CAMERA_RISK = "CAMERA_RISK"
    ANOMALY = "ANOMALY"


class InsightPriority(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ─── Analytics Overview ────────────────────────────────────────────────────────

class AnalyticsOverviewResponse(BaseModel):
    """Aggregated operational summary metrics for selected date range."""
    total_events: int = Field(..., description="Total security events in selected period")
    total_incidents: int = Field(..., description="Total incidents in selected period")
    high_severity_events: int = Field(..., description="Count of HIGH severity events")
    critical_events: int = Field(..., description="Count of CRITICAL severity events")
    resolved_incidents: int = Field(..., description="Count of resolved incidents")
    active_cameras: int = Field(..., description="Count of active cameras in user fleet")
    event_change_percentage: Optional[float] = Field(
        None, description="Percentage change vs prior equivalent period (null if insufficient historical baseline)"
    )
    incident_change_percentage: Optional[float] = Field(
        None, description="Percentage change vs prior equivalent period (null if insufficient historical baseline)"
    )
    period_start: str = Field(..., description="ISO 8601 start timestamp of selected period")
    period_end: str = Field(..., description="ISO 8601 end timestamp of selected period")
    comparison_period_start: Optional[str] = Field(None, description="ISO 8601 start of comparison period")
    comparison_period_end: Optional[str] = Field(None, description="ISO 8601 end of comparison period")


# ─── Event Trends ─────────────────────────────────────────────────────────────

class EventTrendItem(BaseModel):
    """Single time-bucket data point in event trends."""
    timestamp: str = Field(..., description="ISO 8601 timestamp representing bucket start")
    label: str = Field(..., description="Human-readable bucket label (e.g. '14:00', 'Mon 09', 'Week 36')")
    total: int = Field(..., description="Total events in this bucket")
    low: int = Field(0, description="LOW severity events in this bucket")
    medium: int = Field(0, description="MEDIUM severity events in this bucket")
    high: int = Field(0, description="HIGH severity events in this bucket")
    critical: int = Field(0, description="CRITICAL severity events in this bucket")


class EventTrendsResponse(BaseModel):
    """Time-series analytics response with adaptive interval bucket grouping."""
    interval: str = Field(..., description="'hourly' | 'daily' | 'weekly'")
    total_events: int = Field(..., description="Sum of events across all buckets")
    data: List[EventTrendItem] = Field(default_factory=list)


# ─── Distributions ────────────────────────────────────────────────────────────

class DistributionItem(BaseModel):
    """Category count and normalized percentage."""
    name: str = Field(..., description="Category label")
    count: int = Field(..., description="Event count for category")
    percentage: float = Field(..., description="Normalized percentage (0.0 to 100.0)")


class EventDistributionResponse(BaseModel):
    """Distribution of security events grouped by event type."""
    total: int = Field(..., description="Total events analyzed")
    items: List[DistributionItem] = Field(default_factory=list)


class SeverityDistributionItem(BaseModel):
    """Distribution item for severity level."""
    severity: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    count: int = Field(..., description="Event count")
    percentage: float = Field(..., description="Normalized percentage (0.0 to 100.0)")


class SeverityDistributionResponse(BaseModel):
    """Distribution of security events grouped by severity."""
    total: int = Field(..., description="Total events analyzed")
    items: List[SeverityDistributionItem] = Field(default_factory=list)


# ─── Camera Analytics & Deterministic Risk ────────────────────────────────────

class CameraAnalyticsItem(BaseModel):
    """Per-camera operational metrics and explainable risk score."""
    camera_id: str
    camera_name: str
    location: str
    status: str
    is_enabled: bool
    total_events: int
    high_severity_events: int
    critical_events: int
    incidents: int
    avg_events_per_day: float
    most_common_event_type: Optional[str] = None
    last_activity: Optional[str] = None
    risk_score: int = Field(..., ge=0, le=100, description="Deterministic risk score clamped between 0 and 100")
    risk_level: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    risk_factors: List[str] = Field(default_factory=list, description="List of transparent contributing factors")


class CameraAnalyticsResponse(BaseModel):
    """Fleet camera performance and risk ranking."""
    total_cameras: int
    most_active_camera: Optional[str] = None
    highest_risk_camera: Optional[str] = None
    cameras: List[CameraAnalyticsItem] = Field(default_factory=list)


# ─── Security Activity Heatmap ────────────────────────────────────────────────

class HeatmapCell(BaseModel):
    """Day-of-week vs hour-of-day activity matrix cell."""
    day: int = Field(..., ge=0, le=6, description="0 = Monday, 1 = Tuesday, ..., 6 = Sunday")
    day_name: str = Field(..., description="Full day name (Monday..Sunday)")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0..23)")
    count: int = Field(..., ge=0, description="Security event count in this time slot")


class ActivityHeatmapResponse(BaseModel):
    """7x24 Day vs Hour security activity heatmap and detected time patterns."""
    cells: List[HeatmapCell] = Field(default_factory=list)
    peak_hour: Optional[int] = Field(None, description="Hour of day with highest cumulative event activity")
    peak_day: Optional[str] = Field(None, description="Day of week with highest cumulative event activity")
    quiet_hours: List[int] = Field(default_factory=list, description="Hours with historically zero/lowest activity")
    total_events: int = Field(..., description="Total events in heatmap matrix")


# ─── Incident Analytics ───────────────────────────────────────────────────────

class IncidentAnalyticsResponse(BaseModel):
    """Lifecycle analysis for AI incident reports."""
    total_incidents: int
    by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Incidents by operational status (OPEN, INVESTIGATING, RESOLVED, CLOSED)"
    )
    by_risk_level: Dict[str, int] = Field(
        default_factory=dict,
        description="Incidents by AI risk level (LOW, MEDIUM, HIGH, CRITICAL)"
    )
    resolved_count: int
    resolution_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage of resolved/closed incidents")
    average_resolution_time_minutes: Optional[float] = Field(
        None, description="Average time to resolution in minutes (null if no resolved incidents have timestamps)"
    )


# ─── Rule-Based Anomaly Detection ─────────────────────────────────────────────

class AnomalyItem(BaseModel):
    """Single detected operational anomaly with mathematical explanation."""
    id: str
    type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    observed_value: float
    baseline_value: float
    deviation_percentage: float
    detected_at: str
    why_flagged: str
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None


class AnomalyDetectionResponse(BaseModel):
    """Result of rule-based anomaly detection."""
    has_sufficient_data: bool = Field(
        ..., description="True if enough historical baseline data exists for statistical comparison"
    )
    status: str = Field(
        ..., description="'INSUFFICIENT_DATA' | 'NORMAL' | 'ANOMALIES_DETECTED'"
    )
    message: str = Field(..., description="Human-readable operational status explanation")
    anomalies: List[AnomalyItem] = Field(default_factory=list)
    total_anomalies: int = 0


# ─── Operational Security Insights ────────────────────────────────────────────

class SecurityInsightItem(BaseModel):
    """Concise, deterministic operational insight for SOC operators."""
    id: str
    type: InsightType
    priority: InsightPriority
    title: str
    description: str
    related_entity: Optional[str] = None


class SecurityInsightsResponse(BaseModel):
    """Actionable deterministic insights."""
    insights: List[SecurityInsightItem] = Field(default_factory=list)
    total_insights: int = 0
