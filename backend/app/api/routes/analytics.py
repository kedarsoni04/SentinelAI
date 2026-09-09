"""
API Routes for SentinelAI Phase 9 — Advanced Analytics & Anomaly Intelligence.

Namespace: /api/analytics
All endpoints require authentication, validate date ranges, enforce strict
user ownership data isolation, and return typed Pydantic responses.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.schemas.analytics import (
    ActivityHeatmapResponse,
    AnalyticsOverviewResponse,
    AnomalyDetectionResponse,
    CameraAnalyticsResponse,
    DateRangePreset,
    EventDistributionResponse,
    EventTrendsResponse,
    IncidentAnalyticsResponse,
    SecurityInsightsResponse,
    SeverityDistributionResponse,
)
from app.schemas.user import UserResponse
from app.services import analytics_service
from app.services.anomaly_service import detect_operational_anomalies

logger = logging.getLogger("sentinel.api.analytics")

router = APIRouter(prefix="/api/analytics", tags=["Advanced Analytics & Anomaly Intelligence"])


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Aggregated security metrics overview with period comparison",
)
def get_overview(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewResponse:
    c_start, c_end, comp_start, comp_end, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_analytics_overview(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
        comp_start=comp_start,
        comp_end=comp_end,
    )


@router.get(
    "/events/trends",
    response_model=EventTrendsResponse,
    summary="Time-series event trends with multi-severity grouping",
)
def get_trends(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventTrendsResponse:
    c_start, c_end, _, _, interval = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_event_trends(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
        interval=interval,
    )


@router.get(
    "/events/distribution",
    response_model=EventDistributionResponse,
    summary="Event distribution grouped by event type",
)
def get_event_distribution(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventDistributionResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_event_type_distribution(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )


@router.get(
    "/events/severity",
    response_model=SeverityDistributionResponse,
    summary="Security event distribution grouped by severity",
)
def get_severity_distribution(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SeverityDistributionResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_severity_distribution(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )


@router.get(
    "/cameras",
    response_model=CameraAnalyticsResponse,
    summary="Per-camera operational statistics and deterministic risk ranking",
)
def get_camera_analytics(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CameraAnalyticsResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_camera_analytics(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )


@router.get(
    "/activity",
    response_model=ActivityHeatmapResponse,
    summary="7x24 Day vs Hour security activity heatmap and detected time patterns",
)
def get_activity_heatmap(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityHeatmapResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_activity_heatmap(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )


@router.get(
    "/incidents",
    response_model=IncidentAnalyticsResponse,
    summary="Incident lifecycle metrics, resolution rates, and durations",
)
def get_incident_analytics(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncidentAnalyticsResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_incident_analytics(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )


@router.get(
    "/anomalies",
    response_model=AnomalyDetectionResponse,
    summary="Statistical, rule-based anomaly detection with mathematical explanation",
)
def get_anomalies(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnomalyDetectionResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return detect_operational_anomalies(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )


@router.get(
    "/insights",
    response_model=SecurityInsightsResponse,
    summary="Explainable, deterministic operational security insights",
)
def get_insights(
    preset: Optional[DateRangePreset] = Query(DateRangePreset.LAST_7_DAYS, description="Time range preset"),
    start_date: Optional[str] = Query(None, description="ISO 8601 start timestamp for custom range"),
    end_date: Optional[str] = Query(None, description="ISO 8601 end timestamp for custom range"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityInsightsResponse:
    c_start, c_end, _, _, _ = analytics_service.parse_date_range(
        preset.value if preset else "7d", start_date, end_date
    )
    return analytics_service.get_security_insights(
        db=db,
        user_id=current_user.id,
        current_start=c_start,
        current_end=c_end,
    )
