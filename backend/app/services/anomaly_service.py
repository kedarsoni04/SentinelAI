"""
Statistical & Rule-Based Anomaly Detection Service for SentinelAI Phase 9.

Implements explainable, deterministic detection of operational security anomalies:
1. EVENT_VOLUME_SPIKE — Period event count significantly exceeds historical baseline rate.
2. SEVERITY_SPIKE — Unusual surge in HIGH or CRITICAL severity security events.
3. CAMERA_ACTIVITY_SPIKE — Specific camera activity significantly higher than its normal baseline.
4. UNUSUAL_TIME_ACTIVITY — Activity occurring during historically quiet hours.

Guiding Principles:
- Strictly deterministic, mathematical rules (NO AI/LLM models).
- Enforces strict minimum sample requirements before detecting anomalies.
- Safely handles zero baseline and zero division edge cases.
- Anomalies represent unusual operational patterns, NOT criminal intent or threat attribution.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analysis_job import AnalysisJob
from app.models.camera import Camera
from app.models.security_event import SecurityEvent
from app.models.security_rule import SecurityEventSeverity
from app.schemas.analytics import (
    AnomalyDetectionResponse,
    AnomalyItem,
    AnomalySeverity,
    AnomalyType,
)

logger = logging.getLogger("sentinel.services.anomaly")

MIN_BASELINE_EVENTS = 5
MIN_BASELINE_HOURS = 24.0
SPIKE_THRESHOLD_MULTIPLIER = 2.0
CAMERA_SPIKE_MULTIPLIER = 2.5


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def detect_operational_anomalies(
    db: Session,
    user_id: str,
    current_start: datetime,
    current_end: datetime,
) -> AnomalyDetectionResponse:
    """
    Evaluate user's historical event data against the current period to detect
    deterministic operational anomalies.
    """
    current_start = _ensure_utc(current_start)
    current_end = _ensure_utc(current_end)
    current_duration_hours = max((current_end - current_start).total_seconds() / 3600.0, 1.0)

    # Establish baseline window: either equivalent preceding period or up to 30 days prior
    baseline_duration_hours = max(current_duration_hours, MIN_BASELINE_HOURS)
    baseline_start = current_start - timedelta(hours=baseline_duration_hours)
    baseline_end = current_start

    # 1. Check historical baseline sample count for this user
    base_query = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(AnalysisJob.user_id == user_id)
    )

    baseline_event_count = (
        base_query.filter(
            SecurityEvent.created_at >= baseline_start,
            SecurityEvent.created_at < baseline_end,
        ).count()
    )

    # If baseline events are too few, also check total all-time events prior to current period
    if baseline_event_count < MIN_BASELINE_EVENTS:
        total_prior_events = base_query.filter(SecurityEvent.created_at < current_start).count()
        if total_prior_events < MIN_BASELINE_EVENTS:
            return AnomalyDetectionResponse(
                has_sufficient_data=False,
                status="INSUFFICIENT_DATA",
                message="Not enough historical data to detect anomalies yet. Minimum 5 historical events required.",
                anomalies=[],
                total_anomalies=0,
            )

    # 2. Query current period events summary
    current_events_query = base_query.filter(
        SecurityEvent.created_at >= current_start,
        SecurityEvent.created_at <= current_end,
    )
    current_total = current_events_query.count()

    anomalies: List[AnomalyItem] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    # Rate calculations
    effective_baseline_hours = max((baseline_end - baseline_start).total_seconds() / 3600.0, 1.0)
    baseline_hourly_rate = baseline_event_count / effective_baseline_hours
    expected_current_total = baseline_hourly_rate * current_duration_hours

    # ─── Rule 1: EVENT_VOLUME_SPIKE ───────────────────────────────────────────
    # Flag when current event volume exceeds baseline rate by multiplier AND has meaningful count
    if (
        current_total >= 5
        and expected_current_total > 0
        and current_total >= (expected_current_total * SPIKE_THRESHOLD_MULTIPLIER)
    ):
        deviation = round(
            ((current_total - expected_current_total) / max(expected_current_total, 1.0)) * 100.0,
            1,
        )
        severity = AnomalySeverity.HIGH if deviation >= 200.0 else AnomalySeverity.MEDIUM
        anomalies.append(
            AnomalyItem(
                id=str(uuid.uuid4()),
                type=AnomalyType.EVENT_VOLUME_SPIKE,
                severity=severity,
                title="Event Activity Volume Spike",
                description=(
                    f"Event activity ({current_total} events) is {deviation}% above historical baseline "
                    f"for this time duration."
                ),
                observed_value=float(current_total),
                baseline_value=round(expected_current_total, 1),
                deviation_percentage=deviation,
                detected_at=now_iso,
                why_flagged=(
                    f"Current event count ({current_total}) exceeded the statistical baseline threshold "
                    f"({round(expected_current_total * SPIKE_THRESHOLD_MULTIPLIER, 1)} events) with a {SPIKE_THRESHOLD_MULTIPLIER}x multiplier."
                ),
            )
        )

    # ─── Rule 2: SEVERITY_SPIKE ───────────────────────────────────────────────
    # Check for surge in HIGH / CRITICAL events
    baseline_high_crit = (
        base_query.filter(
            SecurityEvent.created_at >= baseline_start,
            SecurityEvent.created_at < baseline_end,
            SecurityEvent.severity.in_([SecurityEventSeverity.HIGH, SecurityEventSeverity.CRITICAL]),
        ).count()
    )
    current_high_crit = (
        current_events_query.filter(
            SecurityEvent.severity.in_([SecurityEventSeverity.HIGH, SecurityEventSeverity.CRITICAL])
        ).count()
    )

    baseline_crit_rate = baseline_high_crit / effective_baseline_hours
    expected_crit = baseline_crit_rate * current_duration_hours

    if (
        current_high_crit >= 3
        and current_high_crit >= max(expected_crit * SPIKE_THRESHOLD_MULTIPLIER, 2.0)
    ):
        baseline_display = max(expected_crit, 0.5)
        deviation = round(((current_high_crit - baseline_display) / baseline_display) * 100.0, 1)
        anomalies.append(
            AnomalyItem(
                id=str(uuid.uuid4()),
                type=AnomalyType.SEVERITY_SPIKE,
                severity=AnomalySeverity.HIGH,
                title="Critical & High Severity Surge",
                description=(
                    f"{current_high_crit} high/critical severity security events recorded, "
                    f"exceeding the baseline expectation."
                ),
                observed_value=float(current_high_crit),
                baseline_value=round(expected_crit, 1),
                deviation_percentage=deviation,
                detected_at=now_iso,
                why_flagged=(
                    f"High and critical severity frequency ({current_high_crit}) is {deviation}% "
                    f"higher than historical baseline ({round(expected_crit, 1)} expected)."
                ),
            )
        )

    # ─── Rule 3: CAMERA_ACTIVITY_SPIKE ────────────────────────────────────────
    # Check individual cameras exceeding their own historical baseline
    user_cameras = db.query(Camera).all()
    for cam in user_cameras:
        cam_base = (
            base_query.filter(
                SecurityEvent.camera_id == cam.id,
                SecurityEvent.created_at >= baseline_start,
                SecurityEvent.created_at < baseline_end,
            ).count()
        )
        cam_curr = (
            current_events_query.filter(SecurityEvent.camera_id == cam.id).count()
        )

        cam_expected = (cam_base / effective_baseline_hours) * current_duration_hours

        if cam_curr >= 4 and cam_curr >= max(cam_expected * CAMERA_SPIKE_MULTIPLIER, 3.0):
            baseline_display = max(cam_expected, 0.5)
            deviation = round(((cam_curr - baseline_display) / baseline_display) * 100.0, 1)
            anomalies.append(
                AnomalyItem(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.CAMERA_ACTIVITY_SPIKE,
                    severity=AnomalySeverity.MEDIUM if deviation < 250 else AnomalySeverity.HIGH,
                    title=f"Camera Activity Spike: {cam.name}",
                    description=(
                        f"Camera '{cam.name}' recorded {cam_curr} events ({deviation}% above its normal baseline)."
                    ),
                    observed_value=float(cam_curr),
                    baseline_value=round(cam_expected, 1),
                    deviation_percentage=deviation,
                    detected_at=now_iso,
                    why_flagged=(
                        f"Activity on '{cam.name}' ({cam_curr} events) exceeded its baseline threshold "
                        f"({round(cam_expected, 1)} expected) by {CAMERA_SPIKE_MULTIPLIER}x."
                    ),
                    camera_id=cam.id,
                    camera_name=cam.name,
                )
            )

    # ─── Rule 4: UNUSUAL_TIME_ACTIVITY ────────────────────────────────────────
    # Group baseline events by hour of day to find historically quiet hours
    baseline_events = (
        base_query.filter(
            SecurityEvent.created_at >= baseline_start,
            SecurityEvent.created_at < baseline_end,
        ).all()
    )

    hour_counts: Dict[int, int] = {h: 0 for h in range(24)}
    for ev in baseline_events:
        if ev.created_at:
            h = ev.created_at.hour
            hour_counts[h] = hour_counts.get(h, 0) + 1

    # Define quiet hours: hours with 0 historical events or < 2% of total baseline events
    quiet_threshold = max(baseline_event_count * 0.02, 1.0)
    quiet_hours = {h for h, c in hour_counts.items() if c <= quiet_threshold}

    # Check current period events occurring during quiet hours
    current_events = current_events_query.all()
    unusual_hour_events: Dict[int, List[SecurityEvent]] = {}
    for ev in current_events:
        if ev.created_at:
            h = ev.created_at.hour
            if h in quiet_hours:
                unusual_hour_events.setdefault(h, []).append(ev)

    for h, evs in unusual_hour_events.items():
        if len(evs) >= 2:  # at least 2 events to avoid single noise trigger
            anomalies.append(
                AnomalyItem(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.UNUSUAL_TIME_ACTIVITY,
                    severity=AnomalySeverity.LOW if len(evs) < 5 else AnomalySeverity.MEDIUM,
                    title=f"Unusual Activity During Off-Peak Hours ({h:02d}:00)",
                    description=(
                        f"{len(evs)} security events occurred during hour {h:02d}:00, "
                        f"a historically quiet operational window."
                    ),
                    observed_value=float(len(evs)),
                    baseline_value=float(hour_counts.get(h, 0)),
                    deviation_percentage=round(
                        ((len(evs) - hour_counts.get(h, 0)) / max(hour_counts.get(h, 1), 1)) * 100.0,
                        1,
                    ),
                    detected_at=now_iso,
                    why_flagged=(
                        f"Hour {h:02d}:00 historically has near-zero activity ({hour_counts.get(h, 0)} events), "
                        f"but recorded {len(evs)} events in the selected period."
                    ),
                )
            )

    if anomalies:
        return AnomalyDetectionResponse(
            has_sufficient_data=True,
            status="ANOMALIES_DETECTED",
            message=f"Detected {len(anomalies)} operational security anomalies.",
            anomalies=anomalies,
            total_anomalies=len(anomalies),
        )
    else:
        return AnomalyDetectionResponse(
            has_sufficient_data=True,
            status="NORMAL",
            message="No unusual activity patterns detected. System is operating within normal baseline parameters.",
            anomalies=[],
            total_anomalies=0,
        )
