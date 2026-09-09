"""
Core Analytics Service for SentinelAI Phase 9.

Responsibilities:
1. Validates and parses time ranges (presets: 24h, 7d, 30d, 90d, custom).
2. Computes operational overview metrics and prior equivalent period comparison.
3. Generates time-series event trends with adaptive bucket intervals.
4. Calculates event type and severity distributions.
5. Computes per-camera performance and deterministic, explainable risk scoring.
6. Aggregates 7x24 Day vs Hour security activity heatmap and time patterns.
7. Analyzes incident lifecycle, resolution rates, and resolution durations.
8. Synthesizes deterministic operational insights for SOC operators.
"""
import calendar
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analysis_job import AnalysisJob
from app.models.camera import Camera
from app.models.incident_report import IncidentOperationalStatus, IncidentReport
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.models.security_rule import SecurityEventSeverity, SecurityEventType
from app.schemas.analytics import (
    ActivityHeatmapResponse,
    AnalyticsOverviewResponse,
    CameraAnalyticsItem,
    CameraAnalyticsResponse,
    DistributionItem,
    EventDistributionResponse,
    EventTrendItem,
    EventTrendsResponse,
    HeatmapCell,
    IncidentAnalyticsResponse,
    InsightPriority,
    InsightType,
    SecurityInsightItem,
    SecurityInsightsResponse,
    SeverityDistributionItem,
    SeverityDistributionResponse,
)
from app.services.anomaly_service import detect_operational_anomalies

logger = logging.getLogger("sentinel.services.analytics")

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime object is timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_date_range(
    preset: Optional[str] = None,
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
) -> Tuple[datetime, datetime, datetime, datetime, str]:
    """
    Parse and validate date range parameters.
    Returns: (current_start, current_end, comp_start, comp_end, interval)
    """
    now = datetime.now(timezone.utc)
    preset_lower = (preset or "7d").lower().strip()

    if preset_lower == "24h":
        current_end = now
        current_start = now - timedelta(hours=24)
        comp_end = current_start
        comp_start = current_start - timedelta(hours=24)
        interval = "hourly"

    elif preset_lower == "7d":
        current_end = now
        current_start = now - timedelta(days=7)
        comp_end = current_start
        comp_start = current_start - timedelta(days=7)
        interval = "daily"

    elif preset_lower == "30d":
        current_end = now
        current_start = now - timedelta(days=30)
        comp_end = current_start
        comp_start = current_start - timedelta(days=30)
        interval = "daily"

    elif preset_lower == "90d":
        current_end = now
        current_start = now - timedelta(days=90)
        comp_end = current_start
        comp_start = current_start - timedelta(days=90)
        interval = "weekly"

    elif preset_lower == "custom":
        if not start_str or not end_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'start_date' and 'end_date' must be provided for custom date ranges.",
            )
        try:
            clean_start = start_str.strip().replace("Z", "+00:00")
            if " " in clean_start and ("T" in clean_start or "+" in clean_start or "-" in clean_start):
                # Starlette unquotes '+' into ' ' in query params
                clean_start = clean_start.replace(" ", "+")
            clean_end = end_str.strip().replace("Z", "+00:00")
            if " " in clean_end and ("T" in clean_end or "+" in clean_end or "-" in clean_end):
                clean_end = clean_end.replace(" ", "+")

            current_start = _ensure_utc(datetime.fromisoformat(clean_start))
            current_end = _ensure_utc(datetime.fromisoformat(clean_end))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ISO 8601 date format: {e}",
            )

        if current_start > current_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date.",
            )

        duration = current_end - current_start
        if duration.days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom date range cannot exceed 365 days.",
            )

        comp_end = current_start
        comp_start = current_start - duration

        if duration.total_seconds() <= 48 * 3600:
            interval = "hourly"
        elif duration.days <= 60:
            interval = "daily"
        else:
            interval = "weekly"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown preset '{preset}'. Choose from: 24h, 7d, 30d, 90d, custom.",
        )

    return current_start, current_end, comp_start, comp_end, interval


# ─── 1. Overview Metrics ──────────────────────────────────────────────────────

def get_analytics_overview(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
    comp_start: datetime,
    comp_end: datetime,
) -> AnalyticsOverviewResponse:
    """Calculate aggregated metrics and prior period comparison."""
    base_events_q = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(AnalysisJob.user_id == user_id)
    )

    # Current period metrics
    curr_events = base_events_q.filter(
        SecurityEvent.created_at >= current_start,
        SecurityEvent.created_at <= current_end,
    )
    total_events = curr_events.count()

    high_severity_events = curr_events.filter(
        SecurityEvent.severity == SecurityEventSeverity.HIGH
    ).count()

    critical_events = curr_events.filter(
        SecurityEvent.severity == SecurityEventSeverity.CRITICAL
    ).count()

    # Incidents in current period
    incidents_q = db.query(IncidentReport).filter(IncidentReport.user_id == user_id)
    curr_incidents = incidents_q.filter(
        IncidentReport.created_at >= current_start,
        IncidentReport.created_at <= current_end,
    )
    total_incidents = curr_incidents.count()

    resolved_incidents = curr_incidents.filter(
        IncidentReport.incident_status.in_([
            IncidentOperationalStatus.RESOLVED,
            IncidentOperationalStatus.CLOSED,
        ])
    ).count()

    # Active cameras
    active_cameras = db.query(Camera).filter(Camera.is_enabled.is_(True)).count()

    # Prior equivalent period metrics
    comp_events = base_events_q.filter(
        SecurityEvent.created_at >= comp_start,
        SecurityEvent.created_at < comp_end,
    ).count()

    comp_incidents = incidents_q.filter(
        IncidentReport.created_at >= comp_start,
        IncidentReport.created_at < comp_end,
    ).count()

    # Safe percentage comparisons
    event_change_pct = None
    if comp_events > 0:
        event_change_pct = round(((total_events - comp_events) / comp_events) * 100.0, 1)

    incident_change_pct = None
    if comp_incidents > 0:
        incident_change_pct = round(((total_incidents - comp_incidents) / comp_incidents) * 100.0, 1)

    return AnalyticsOverviewResponse(
        total_events=total_events,
        total_incidents=total_incidents,
        high_severity_events=high_severity_events,
        critical_events=critical_events,
        resolved_incidents=resolved_incidents,
        active_cameras=active_cameras,
        event_change_percentage=event_change_pct,
        incident_change_percentage=incident_change_pct,
        period_start=current_start.isoformat(),
        period_end=current_end.isoformat(),
        comparison_period_start=comp_start.isoformat(),
        comparison_period_end=comp_end.isoformat(),
    )


# ─── 2. Event Trends ──────────────────────────────────────────────────────────

def get_event_trends(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
    interval: str,
) -> EventTrendsResponse:
    """Generate time-series buckets with severity breakdown."""
    events = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(
            AnalysisJob.user_id == user_id,
            SecurityEvent.created_at >= current_start,
            SecurityEvent.created_at <= current_end,
        )
        .order_by(SecurityEvent.created_at.asc())
        .all()
    )

    buckets: List[EventTrendItem] = []

    if interval == "hourly":
        # Generate bucket for each hour
        curr = current_start.replace(minute=0, second=0, microsecond=0)
        while curr <= current_end:
            next_hour = curr + timedelta(hours=1)
            bucket_events = [
                e for e in events
                if e.created_at and curr <= _ensure_utc(e.created_at) < next_hour
            ]
            buckets.append(
                EventTrendItem(
                    timestamp=curr.isoformat(),
                    label=curr.strftime("%H:%M"),
                    total=len(bucket_events),
                    low=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.LOW),
                    medium=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.MEDIUM),
                    high=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.HIGH),
                    critical=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.CRITICAL),
                )
            )
            curr = next_hour

    elif interval == "daily":
        curr = current_start.replace(hour=0, minute=0, second=0, microsecond=0)
        while curr <= current_end:
            next_day = curr + timedelta(days=1)
            bucket_events = [
                e for e in events
                if e.created_at and curr <= _ensure_utc(e.created_at) < next_day
            ]
            buckets.append(
                EventTrendItem(
                    timestamp=curr.isoformat(),
                    label=curr.strftime("%b %d"),
                    total=len(bucket_events),
                    low=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.LOW),
                    medium=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.MEDIUM),
                    high=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.HIGH),
                    critical=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.CRITICAL),
                )
            )
            curr = next_day

    else:  # weekly
        curr = current_start.replace(hour=0, minute=0, second=0, microsecond=0)
        while curr <= current_end:
            next_week = curr + timedelta(days=7)
            bucket_events = [
                e for e in events
                if e.created_at and curr <= _ensure_utc(e.created_at) < next_week
            ]
            buckets.append(
                EventTrendItem(
                    timestamp=curr.isoformat(),
                    label=curr.strftime("W%U (%b %d)"),
                    total=len(bucket_events),
                    low=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.LOW),
                    medium=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.MEDIUM),
                    high=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.HIGH),
                    critical=sum(1 for e in bucket_events if e.severity == SecurityEventSeverity.CRITICAL),
                )
            )
            curr = next_week

    return EventTrendsResponse(
        interval=interval,
        total_events=len(events),
        data=buckets,
    )


# ─── 3. Event Distributions ───────────────────────────────────────────────────

def get_event_type_distribution(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> EventDistributionResponse:
    """Distribution of security events by event type."""
    results = (
        db.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(
            AnalysisJob.user_id == user_id,
            SecurityEvent.created_at >= current_start,
            SecurityEvent.created_at <= current_end,
        )
        .group_by(SecurityEvent.event_type)
        .all()
    )

    total = sum(count for _, count in results)
    items: List[DistributionItem] = []
    for etype, count in results:
        etype_name = etype.value if hasattr(etype, "value") else str(etype)
        pct = round((count / total) * 100.0, 1) if total > 0 else 0.0
        items.append(DistributionItem(name=etype_name, count=count, percentage=pct))

    items.sort(key=lambda x: x.count, reverse=True)
    return EventDistributionResponse(total=total, items=items)


def get_severity_distribution(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> SeverityDistributionResponse:
    """Distribution of security events by severity level."""
    results = dict(
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(
            AnalysisJob.user_id == user_id,
            SecurityEvent.created_at >= current_start,
            SecurityEvent.created_at <= current_end,
        )
        .group_by(SecurityEvent.severity)
        .all()
    )

    total = sum(results.values())
    items: List[SeverityDistributionItem] = []
    for sev in [
        SecurityEventSeverity.LOW,
        SecurityEventSeverity.MEDIUM,
        SecurityEventSeverity.HIGH,
        SecurityEventSeverity.CRITICAL,
    ]:
        count = results.get(sev, 0)
        pct = round((count / total) * 100.0, 1) if total > 0 else 0.0
        items.append(
            SeverityDistributionItem(
                severity=sev.value,
                count=count,
                percentage=pct,
            )
        )

    return SeverityDistributionResponse(total=total, items=items)


# ─── 4. Camera Analytics & Deterministic Risk ─────────────────────────────────

def _compute_camera_risk_score(
    high_events: int,
    crit_events: int,
    open_incidents: int,
    avg_events_per_day: float,
) -> Tuple[int, str, List[str]]:
    """
    Deterministic operational risk score formula:
    Risk = min(100, 5*High + 15*Crit + 10*OpenIncidents + min(20, int(avg_daily * 2)))

    Fully explainable and documented. Clamped [0, 100].
    """
    score = 0
    factors: List[str] = []

    if crit_events > 0:
        pts = crit_events * 15
        score += pts
        factors.append(f"{crit_events} critical security event{'s' if crit_events > 1 else ''} (+{pts} pts)")

    if high_events > 0:
        pts = high_events * 5
        score += pts
        factors.append(f"{high_events} high-severity event{'s' if high_events > 1 else ''} (+{pts} pts)")

    if open_incidents > 0:
        pts = open_incidents * 10
        score += pts
        factors.append(f"{open_incidents} active unresolved incident{'s' if open_incidents > 1 else ''} (+{pts} pts)")

    if avg_events_per_day >= 2.0:
        pts = min(int(avg_events_per_day * 2), 20)
        score += pts
        factors.append(f"Elevated frequency: {avg_events_per_day} events/day (+{pts} pts)")

    score = min(score, 100)

    if not factors:
        factors.append("Nominal operational state — no significant risk factors observed (0 pts)")

    if score >= 75:
        level = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level, factors


def get_camera_analytics(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> CameraAnalyticsResponse:
    """Per-camera operational statistics and risk scoring."""
    cameras = db.query(Camera).all()
    duration_days = max((current_end - current_start).days, 1)

    items: List[CameraAnalyticsItem] = []

    for cam in cameras:
        # User events for this camera in current period
        cam_events = (
            db.query(SecurityEvent)
            .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
            .filter(
                AnalysisJob.user_id == user_id,
                SecurityEvent.camera_id == cam.id,
                SecurityEvent.created_at >= current_start,
                SecurityEvent.created_at <= current_end,
            )
            .all()
        )

        total_evs = len(cam_events)
        high_evs = sum(1 for e in cam_events if e.severity == SecurityEventSeverity.HIGH)
        crit_evs = sum(1 for e in cam_events if e.severity == SecurityEventSeverity.CRITICAL)

        # Open incidents for this camera
        open_incidents = (
            db.query(IncidentReport)
            .filter(
                IncidentReport.user_id == user_id,
                IncidentReport.camera_id == cam.id,
                IncidentReport.incident_status.in_([
                    IncidentOperationalStatus.OPEN,
                    IncidentOperationalStatus.INVESTIGATING,
                ]),
            )
            .count()
        )

        # Most common event type
        type_counts: Dict[str, int] = {}
        for e in cam_events:
            t = e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type)
            type_counts[t] = type_counts.get(t, 0) + 1

        most_common = max(type_counts, key=type_counts.get) if type_counts else None

        avg_daily = round(total_evs / duration_days, 1)
        last_act = max((e.created_at for e in cam_events if e.created_at), default=None)

        risk_score, risk_lvl, risk_factors = _compute_camera_risk_score(
            high_events=high_evs,
            crit_events=crit_evs,
            open_incidents=open_incidents,
            avg_events_per_day=avg_daily,
        )

        items.append(
            CameraAnalyticsItem(
                camera_id=cam.id,
                camera_name=cam.name,
                location=cam.location,
                status=cam.status.value if hasattr(cam.status, "value") else str(cam.status),
                is_enabled=cam.is_enabled,
                total_events=total_evs,
                high_severity_events=high_evs,
                critical_events=crit_evs,
                incidents=open_incidents,
                avg_events_per_day=avg_daily,
                most_common_event_type=most_common,
                last_activity=last_act.isoformat() if last_act else None,
                risk_score=risk_score,
                risk_level=risk_lvl,
                risk_factors=risk_factors,
            )
        )

    # Sort cameras by risk_score desc, then total_events desc
    items.sort(key=lambda c: (c.risk_score, c.total_events), reverse=True)

    most_active = max(items, key=lambda c: c.total_events).camera_name if items and any(c.total_events > 0 for c in items) else None
    highest_risk = max(items, key=lambda c: c.risk_score).camera_name if items and any(c.risk_score > 0 for c in items) else None

    return CameraAnalyticsResponse(
        total_cameras=len(items),
        most_active_camera=most_active,
        highest_risk_camera=highest_risk,
        cameras=items,
    )


# ─── 5. Security Activity Heatmap ─────────────────────────────────────────────

def get_activity_heatmap(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> ActivityHeatmapResponse:
    """7-day x 24-hour security activity matrix."""
    events = (
        db.query(SecurityEvent.created_at)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(
            AnalysisJob.user_id == user_id,
            SecurityEvent.created_at >= current_start,
            SecurityEvent.created_at <= current_end,
        )
        .all()
    )

    # Initialize 7x24 grid: day 0 (Monday) to 6 (Sunday), hours 0 to 23
    matrix: Dict[Tuple[int, int], int] = {
        (d, h): 0 for d in range(7) for h in range(24)
    }

    hourly_cumulative: Dict[int, int] = {h: 0 for h in range(24)}
    daily_cumulative: Dict[int, int] = {d: 0 for d in range(7)}

    for (created_at,) in events:
        if created_at:
            dt_utc = _ensure_utc(created_at)
            day = dt_utc.weekday()  # 0 is Monday, 6 is Sunday
            hour = dt_utc.hour
            matrix[(day, hour)] += 1
            hourly_cumulative[hour] += 1
            daily_cumulative[day] += 1

    cells: List[HeatmapCell] = [
        HeatmapCell(
            day=d,
            day_name=DAY_NAMES[d],
            hour=h,
            count=matrix[(d, h)],
        )
        for d in range(7)
        for h in range(24)
    ]

    total = len(events)
    peak_hour = max(hourly_cumulative, key=hourly_cumulative.get) if total > 0 else None
    peak_day_idx = max(daily_cumulative, key=daily_cumulative.get) if total > 0 else None
    peak_day = DAY_NAMES[peak_day_idx] if peak_day_idx is not None else None

    # Identify quiet hours (bottom quartile or 0 count)
    quiet_threshold = max(total * 0.02, 0)
    quiet_hours = [h for h, c in hourly_cumulative.items() if c <= quiet_threshold]

    return ActivityHeatmapResponse(
        cells=cells,
        peak_hour=peak_hour,
        peak_day=peak_day,
        quiet_hours=sorted(quiet_hours),
        total_events=total,
    )


# ─── 6. Incident Analytics ────────────────────────────────────────────────────

def get_incident_analytics(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> IncidentAnalyticsResponse:
    """Incident metrics, status breakdown, and resolution durations."""
    incidents = (
        db.query(IncidentReport)
        .filter(
            IncidentReport.user_id == user_id,
            IncidentReport.created_at >= current_start,
            IncidentReport.created_at <= current_end,
        )
        .all()
    )

    by_status: Dict[str, int] = {
        IncidentOperationalStatus.OPEN.value: 0,
        IncidentOperationalStatus.INVESTIGATING.value: 0,
        IncidentOperationalStatus.RESOLVED.value: 0,
        IncidentOperationalStatus.CLOSED.value: 0,
    }
    by_risk: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    resolution_durations_min: List[float] = []

    for inc in incidents:
        st = inc.incident_status or IncidentOperationalStatus.OPEN.value
        by_status[st] = by_status.get(st, 0) + 1

        if inc.risk_level:
            rl = inc.risk_level.upper()
            by_risk[rl] = by_risk.get(rl, 0) + 1

        if inc.resolved_at and inc.created_at:
            delta = (_ensure_utc(inc.resolved_at) - _ensure_utc(inc.created_at)).total_seconds() / 60.0
            if delta >= 0:
                resolution_durations_min.append(delta)

    total = len(incidents)
    resolved_count = (
        by_status.get(IncidentOperationalStatus.RESOLVED.value, 0)
        + by_status.get(IncidentOperationalStatus.CLOSED.value, 0)
    )
    resolution_rate = round((resolved_count / total) * 100.0, 1) if total > 0 else 0.0

    avg_res_time = None
    if resolution_durations_min:
        avg_res_time = round(sum(resolution_durations_min) / len(resolution_durations_min), 1)

    return IncidentAnalyticsResponse(
        total_incidents=total,
        by_status=by_status,
        by_risk_level=by_risk,
        resolved_count=resolved_count,
        resolution_rate=resolution_rate,
        average_resolution_time_minutes=avg_res_time,
    )


# ─── 7. Operational Security Insights ─────────────────────────────────────────

def get_security_insights(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> SecurityInsightsResponse:
    """Synthesize explainable, deterministic operational insights for SOC operators."""
    insights: List[SecurityInsightItem] = []

    cam_analytics = get_camera_analytics(db, user_id, current_start, current_end)
    dist = get_event_type_distribution(db, user_id, current_start, current_end)
    heatmap = get_activity_heatmap(db, user_id, current_start, current_end)
    anomalies = detect_operational_anomalies(db, user_id, current_start, current_end)

    # 1. Top Camera Insight
    if cam_analytics.most_active_camera and cam_analytics.cameras:
        top_cam = cam_analytics.cameras[0]
        if top_cam.total_events > 0:
            insights.append(
                SecurityInsightItem(
                    id=str(uuid.uuid4()),
                    type=InsightType.TOP_CAMERA,
                    priority=InsightPriority.INFO,
                    title="Primary Activity Hub",
                    description=(
                        f"'{top_cam.camera_name}' ({top_cam.location}) recorded the highest security volume "
                        f"with {top_cam.total_events} events ({top_cam.avg_events_per_day} events/day)."
                    ),
                    related_entity=top_cam.camera_id,
                )
            )

    # 2. Camera Risk Warning
    for cam in cam_analytics.cameras:
        if cam.risk_score >= 50:
            insights.append(
                SecurityInsightItem(
                    id=str(uuid.uuid4()),
                    type=InsightType.CAMERA_RISK,
                    priority=InsightPriority.HIGH if cam.risk_score >= 75 else InsightPriority.MEDIUM,
                    title=f"Elevated Risk: {cam.camera_name}",
                    description=(
                        f"Risk score reached {cam.risk_score}/100 ({cam.risk_level}). "
                        f"Factors: {'; '.join(cam.risk_factors[:2])}."
                    ),
                    related_entity=cam.camera_id,
                )
            )
            break

    # 3. Top Event Type
    if dist.items and dist.total > 0:
        top_type = dist.items[0]
        insights.append(
            SecurityInsightItem(
                id=str(uuid.uuid4()),
                type=InsightType.TOP_EVENT_TYPE,
                priority=InsightPriority.INFO,
                title="Prevalent Event Category",
                description=(
                    f"'{top_type.name}' is the most frequent security event, representing "
                    f"{top_type.percentage}% ({top_type.count} occurrences) of detected activity."
                ),
                related_entity=top_type.name,
            )
        )

    # 4. Peak Activity Time
    if heatmap.peak_hour is not None and heatmap.total_events > 0:
        peak_str = f"{heatmap.peak_hour:02d}:00"
        insights.append(
            SecurityInsightItem(
                id=str(uuid.uuid4()),
                type=InsightType.PEAK_ACTIVITY_TIME,
                priority=InsightPriority.LOW,
                title="Peak Surveillance Window",
                description=(
                    f"Surveillance traffic peaks around {peak_str}"
                    + (f" with highest cumulative volume on {heatmap.peak_day}s." if heatmap.peak_day else ".")
                ),
            )
        )

    # 5. Anomaly alerts
    for a in anomalies.anomalies[:2]:
        insights.append(
            SecurityInsightItem(
                id=str(uuid.uuid4()),
                type=InsightType.ANOMALY,
                priority=InsightPriority.HIGH if a.severity.value in ("HIGH", "CRITICAL") else InsightPriority.MEDIUM,
                title=f"Operational Anomaly: {a.title}",
                description=f"{a.description} {a.why_flagged}",
                related_entity=a.camera_id,
            )
        )

    return SecurityInsightsResponse(
        insights=insights,
        total_insights=len(insights),
    )
