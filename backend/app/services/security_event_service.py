import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analysis_job import AnalysisJob
from app.models.analysis_result import AnalysisResult
from app.models.camera import Camera
from app.models.security_event import SecurityEvent, SecurityEventStatus
from app.models.security_rule import SecurityEventSeverity, SecurityEventType, SecurityRule
from app.models.security_zone import SecurityZone, ZoneType
from app.schemas.security_event import (
    EventMetricsResponse,
    SecurityEventResponse,
    SecurityRuleCreate,
    SecurityRuleResponse,
    SecurityRuleUpdate,
    SecurityZoneCreate,
    SecurityZoneResponse,
    SecurityZoneUpdate,
)
from app.vision.events.geometry import validate_polygon_coordinates

logger = logging.getLogger("sentinel.services.security_events")


# ─── Helper Functions ────────────────────────────────────────────────────────

def _assert_camera_ownership(db: Session, camera_id: Optional[str]) -> Optional[Camera]:
    """Validate camera existence if specified."""
    if not camera_id:
        return None
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found.",
        )
    return cam


# ─── Security Zone Service ───────────────────────────────────────────────────

def create_security_zone(db: Session, user_id: str, data: SecurityZoneCreate) -> SecurityZone:
    """Create a new geometric security zone."""
    is_valid, err = validate_polygon_coordinates([p.model_dump() for p in data.coordinates])
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err,
        )

    _assert_camera_ownership(db, data.camera_id)

    zone = SecurityZone(
        user_id=user_id,
        camera_id=data.camera_id,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
        zone_type=data.zone_type,
        coordinates=[p.model_dump() for p in data.coordinates],
        is_enabled=data.is_enabled,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def get_security_zones(
    db: Session,
    user_id: str,
    camera_id: Optional[str] = None,
) -> List[SecurityZone]:
    """Retrieve all security zones belonging to a user with optional camera filter."""
    query = db.query(SecurityZone).filter(SecurityZone.user_id == user_id)
    if camera_id:
        query = query.filter(SecurityZone.camera_id == camera_id)
    return query.order_by(SecurityZone.created_at.desc()).all()


def get_security_zone_by_id(db: Session, user_id: str, zone_id: str) -> SecurityZone:
    """Retrieve a single security zone enforcing ownership."""
    zone = (
        db.query(SecurityZone)
        .filter(SecurityZone.id == zone_id, SecurityZone.user_id == user_id)
        .first()
    )
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security zone not found.",
        )
    return zone


def update_security_zone(
    db: Session, user_id: str, zone_id: str, data: SecurityZoneUpdate
) -> SecurityZone:
    """Update a security zone's configuration."""
    zone = get_security_zone_by_id(db, user_id, zone_id)

    if data.coordinates is not None:
        is_valid, err = validate_polygon_coordinates([p.model_dump() for p in data.coordinates])
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err,
            )
        zone.coordinates = [p.model_dump() for p in data.coordinates]

    if data.name is not None:
        zone.name = data.name.strip()
    if data.description is not None:
        zone.description = data.description.strip() if data.description else None
    if data.camera_id is not None:
        _assert_camera_ownership(db, data.camera_id)
        zone.camera_id = data.camera_id
    if data.zone_type is not None:
        zone.zone_type = data.zone_type
    if data.is_enabled is not None:
        zone.is_enabled = data.is_enabled

    db.commit()
    db.refresh(zone)
    return zone


def delete_security_zone(db: Session, user_id: str, zone_id: str) -> None:
    """Delete a security zone."""
    zone = get_security_zone_by_id(db, user_id, zone_id)
    db.delete(zone)
    db.commit()


# ─── Security Rule Service ───────────────────────────────────────────────────

def create_security_rule(db: Session, user_id: str, data: SecurityRuleCreate) -> SecurityRule:
    """Create a new configurable security rule."""
    _assert_camera_ownership(db, data.camera_id)

    # Validate zone requirement
    zone = None
    if data.zone_id:
        zone = (
            db.query(SecurityZone)
            .filter(SecurityZone.id == data.zone_id, SecurityZone.user_id == user_id)
            .first()
        )
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referenced security zone not found.",
            )

    # Zone-required rules must specify a valid zone
    if data.event_type in (SecurityEventType.INTRUSION, SecurityEventType.LOITERING, SecurityEventType.CROWD_DENSITY):
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event type '{data.event_type.value}' requires a configured security zone.",
            )

    # Validate numerical thresholds
    if data.threshold_seconds is not None and data.threshold_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold seconds must be strictly positive.",
        )
    if data.threshold_value is not None and data.threshold_value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold value must be strictly positive.",
        )

    rule = SecurityRule(
        user_id=user_id,
        camera_id=data.camera_id,
        zone_id=data.zone_id,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
        event_type=data.event_type,
        severity=data.severity,
        is_enabled=data.is_enabled,
        threshold_value=data.threshold_value,
        threshold_seconds=data.threshold_seconds,
        minimum_confidence=data.minimum_confidence,
        class_filters=data.class_filters,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_security_rules(
    db: Session,
    user_id: str,
    camera_id: Optional[str] = None,
    event_type: Optional[SecurityEventType] = None,
) -> List[SecurityRule]:
    """Retrieve all rules for a user with optional filters."""
    query = db.query(SecurityRule).filter(SecurityRule.user_id == user_id)
    if camera_id:
        query = query.filter(SecurityRule.camera_id == camera_id)
    if event_type:
        query = query.filter(SecurityRule.event_type == event_type)
    return query.order_by(SecurityRule.created_at.desc()).all()


def get_security_rule_by_id(db: Session, user_id: str, rule_id: str) -> SecurityRule:
    """Retrieve a single rule with ownership validation."""
    rule = (
        db.query(SecurityRule)
        .filter(SecurityRule.id == rule_id, SecurityRule.user_id == user_id)
        .first()
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security rule not found.",
        )
    return rule


def update_security_rule(
    db: Session, user_id: str, rule_id: str, data: SecurityRuleUpdate
) -> SecurityRule:
    """Update an existing security rule."""
    rule = get_security_rule_by_id(db, user_id, rule_id)

    if data.name is not None:
        rule.name = data.name.strip()
    if data.description is not None:
        rule.description = data.description.strip() if data.description else None
    if data.severity is not None:
        rule.severity = data.severity
    if data.camera_id is not None:
        _assert_camera_ownership(db, data.camera_id)
        rule.camera_id = data.camera_id
    if data.zone_id is not None:
        zone = (
            db.query(SecurityZone)
            .filter(SecurityZone.id == data.zone_id, SecurityZone.user_id == user_id)
            .first()
        )
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referenced security zone not found.",
            )
        rule.zone_id = data.zone_id
    if data.threshold_value is not None:
        if data.threshold_value <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Threshold value must be > 0.")
        rule.threshold_value = data.threshold_value
    if data.threshold_seconds is not None:
        if data.threshold_seconds <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Threshold seconds must be > 0.")
        rule.threshold_seconds = data.threshold_seconds
    if data.minimum_confidence is not None:
        rule.minimum_confidence = data.minimum_confidence
    if data.class_filters is not None:
        rule.class_filters = data.class_filters
    if data.is_enabled is not None:
        rule.is_enabled = data.is_enabled

    db.commit()
    db.refresh(rule)
    return rule


def delete_security_rule(db: Session, user_id: str, rule_id: str) -> None:
    """Delete a security rule."""
    rule = get_security_rule_by_id(db, user_id, rule_id)
    db.delete(rule)
    db.commit()


# ─── Security Event Service ──────────────────────────────────────────────────

def _build_event_response(ev: SecurityEvent) -> SecurityEventResponse:
    """Helper to convert SecurityEvent ORM to SecurityEventResponse schema with URLs."""
    evidence_url = None
    annotated_url = None
    if ev.evidence_frame:
        filename = f"frame_{ev.evidence_frame.frame_index:06d}.jpg"
        evidence_url = f"/api/video-analysis/{ev.analysis_job_id}/frames/{filename}"
        if ev.evidence_frame.annotated_frame_path:
            ann_filename = f"annotated_{ev.evidence_frame.frame_index:06d}.jpg"
            annotated_url = f"/api/video-analysis/{ev.analysis_job_id}/annotated/{ann_filename}"

    camera_name = ev.camera.name if ev.camera else None
    rule_name = ev.rule.name if ev.rule else None

    return SecurityEventResponse(
        id=ev.id,
        analysis_job_id=ev.analysis_job_id,
        camera_id=ev.camera_id,
        camera_name=camera_name,
        rule_id=ev.rule_id,
        rule_name=rule_name,
        tracked_object_id=ev.tracked_object_id,
        track_id=ev.track_id,
        class_name=ev.class_name,
        event_type=ev.event_type,
        severity=ev.severity,
        status=ev.status.value,
        title=ev.title,
        description=ev.description,
        start_timestamp=round(ev.start_timestamp, 2),
        end_timestamp=round(ev.end_timestamp, 2) if ev.end_timestamp is not None else None,
        duration_seconds=round(ev.duration_seconds, 2) if ev.duration_seconds is not None else None,
        confidence=round(ev.confidence, 4) if ev.confidence is not None else None,
        evidence_frame_id=ev.evidence_frame_id,
        evidence_frame_url=evidence_url,
        annotated_frame_url=annotated_url,
        metadata_json=ev.metadata_json,
        created_at=ev.created_at.isoformat(),
        updated_at=ev.updated_at.isoformat(),
    )


def get_security_events(
    db: Session,
    user_id: str,
    event_type: Optional[SecurityEventType] = None,
    severity: Optional[SecurityEventSeverity] = None,
    status_filter: Optional[str] = None,
    camera_id: Optional[str] = None,
    analysis_job_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[SecurityEventResponse]:
    """Retrieve security events filtered by user ownership via AnalysisJob."""
    query = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(AnalysisJob.user_id == user_id)
    )

    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if status_filter:
        stat_upper = status_filter.upper().strip()
        if stat_upper in SecurityEventStatus.__members__:
            query = query.filter(SecurityEvent.status == SecurityEventStatus[stat_upper])
    if camera_id:
        query = query.filter(SecurityEvent.camera_id == camera_id)
    if analysis_job_id:
        query = query.filter(SecurityEvent.analysis_job_id == analysis_job_id)

    events = (
        query.order_by(SecurityEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_build_event_response(ev) for ev in events]


def get_security_event_by_id(
    db: Session, user_id: str, event_id: str
) -> SecurityEventResponse:
    """Retrieve detailed event with ownership validation."""
    ev = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(SecurityEvent.id == event_id, AnalysisJob.user_id == user_id)
        .first()
    )
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security event not found.",
        )
    return _build_event_response(ev)


def update_event_status(
    db: Session, user_id: str, event_id: str, new_status_str: str
) -> SecurityEventResponse:
    """Transition an event's workflow status (OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED)."""
    ev = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(SecurityEvent.id == event_id, AnalysisJob.user_id == user_id)
        .first()
    )
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security event not found.",
        )

    target_status = new_status_str.upper().strip()
    if target_status not in SecurityEventStatus.__members__:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event status '{new_status_str}'. Allowed: OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED.",
        )

    ev.status = SecurityEventStatus[target_status]
    db.commit()
    db.refresh(ev)
    return _build_event_response(ev)


def get_event_metrics(db: Session, user_id: str) -> EventMetricsResponse:
    """Calculate aggregated metrics for the SOC dashboard."""
    user_events = (
        db.query(SecurityEvent)
        .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
        .filter(AnalysisJob.user_id == user_id)
    )

    total = user_events.count()
    open_count = user_events.filter(SecurityEvent.status == SecurityEventStatus.OPEN).count()
    high_count = user_events.filter(SecurityEvent.severity == SecurityEventSeverity.HIGH).count()
    med_count = user_events.filter(SecurityEvent.severity == SecurityEventSeverity.MEDIUM).count()
    low_count = user_events.filter(SecurityEvent.severity == SecurityEventSeverity.LOW).count()

    # Events created today (UTC start of day)
    now_utc = datetime.now(timezone.utc)
    today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    today_count = user_events.filter(SecurityEvent.created_at >= today_start).count()

    # Breakdown by event type
    by_type: Dict[str, int] = {}
    for ev_type in SecurityEventType:
        c = user_events.filter(SecurityEvent.event_type == ev_type).count()
        by_type[ev_type.value] = c

    return EventMetricsResponse(
        total_events=total,
        open_events=open_count,
        high_severity_events=high_count,
        medium_severity_events=med_count,
        low_severity_events=low_count,
        events_today=today_count,
        by_type=by_type,
    )
