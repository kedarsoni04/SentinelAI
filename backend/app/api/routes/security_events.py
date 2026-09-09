from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.security_rule import SecurityEventSeverity, SecurityEventType
from app.schemas.security_event import (
    EventMetricsResponse,
    SecurityEventResponse,
    SecurityEventStatusUpdate,
    SecurityRuleCreate,
    SecurityRuleResponse,
    SecurityRuleUpdate,
    SecurityZoneCreate,
    SecurityZoneResponse,
    SecurityZoneUpdate,
)
from app.schemas.user import UserResponse
from app.services import security_event_service

router = APIRouter(tags=["Security Events & Rules"])


# ─── Security Zones ──────────────────────────────────────────────────────────

@router.get(
    "/api/security-zones",
    response_model=List[SecurityZoneResponse],
    summary="List all security zones for authenticated user",
)
def list_zones(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SecurityZoneResponse]:
    zones = security_event_service.get_security_zones(db, current_user.id, camera_id)
    return [
        SecurityZoneResponse(
            id=z.id,
            user_id=z.user_id,
            camera_id=z.camera_id,
            camera_name=z.camera.name if z.camera else None,
            name=z.name,
            description=z.description,
            zone_type=z.zone_type,
            coordinates=z.coordinates,
            is_enabled=z.is_enabled,
            created_at=z.created_at.isoformat(),
            updated_at=z.updated_at.isoformat(),
        )
        for z in zones
    ]


@router.post(
    "/api/security-zones",
    response_model=SecurityZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new security zone",
)
def create_zone(
    data: SecurityZoneCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityZoneResponse:
    z = security_event_service.create_security_zone(db, current_user.id, data)
    return SecurityZoneResponse(
        id=z.id,
        user_id=z.user_id,
        camera_id=z.camera_id,
        camera_name=z.camera.name if z.camera else None,
        name=z.name,
        description=z.description,
        zone_type=z.zone_type,
        coordinates=z.coordinates,
        is_enabled=z.is_enabled,
        created_at=z.created_at.isoformat(),
        updated_at=z.updated_at.isoformat(),
    )


@router.get(
    "/api/security-zones/{zone_id}",
    response_model=SecurityZoneResponse,
    summary="Retrieve a security zone by ID",
)
def get_zone(
    zone_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityZoneResponse:
    z = security_event_service.get_security_zone_by_id(db, current_user.id, zone_id)
    return SecurityZoneResponse(
        id=z.id,
        user_id=z.user_id,
        camera_id=z.camera_id,
        camera_name=z.camera.name if z.camera else None,
        name=z.name,
        description=z.description,
        zone_type=z.zone_type,
        coordinates=z.coordinates,
        is_enabled=z.is_enabled,
        created_at=z.created_at.isoformat(),
        updated_at=z.updated_at.isoformat(),
    )


@router.put(
    "/api/security-zones/{zone_id}",
    response_model=SecurityZoneResponse,
    summary="Update an existing security zone",
)
def update_zone(
    zone_id: str,
    data: SecurityZoneUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityZoneResponse:
    z = security_event_service.update_security_zone(db, current_user.id, zone_id, data)
    return SecurityZoneResponse(
        id=z.id,
        user_id=z.user_id,
        camera_id=z.camera_id,
        camera_name=z.camera.name if z.camera else None,
        name=z.name,
        description=z.description,
        zone_type=z.zone_type,
        coordinates=z.coordinates,
        is_enabled=z.is_enabled,
        created_at=z.created_at.isoformat(),
        updated_at=z.updated_at.isoformat(),
    )


@router.patch(
    "/api/security-zones/{zone_id}/status",
    response_model=SecurityZoneResponse,
    summary="Quick toggle a security zone enabled status",
)
def toggle_zone_status(
    zone_id: str,
    is_enabled: bool = Query(..., description="Target enabled state"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityZoneResponse:
    z = security_event_service.update_security_zone(
        db, current_user.id, zone_id, SecurityZoneUpdate(is_enabled=is_enabled)
    )
    return SecurityZoneResponse(
        id=z.id,
        user_id=z.user_id,
        camera_id=z.camera_id,
        camera_name=z.camera.name if z.camera else None,
        name=z.name,
        description=z.description,
        zone_type=z.zone_type,
        coordinates=z.coordinates,
        is_enabled=z.is_enabled,
        created_at=z.created_at.isoformat(),
        updated_at=z.updated_at.isoformat(),
    )


@router.delete(
    "/api/security-zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a security zone",
)
def delete_zone(
    zone_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    security_event_service.delete_security_zone(db, current_user.id, zone_id)


# ─── Security Rules ──────────────────────────────────────────────────────────

@router.get(
    "/api/security-rules",
    response_model=List[SecurityRuleResponse],
    summary="List all security rules for authenticated user",
)
def list_rules(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    event_type: Optional[SecurityEventType] = Query(None, description="Filter by event type"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SecurityRuleResponse]:
    rules = security_event_service.get_security_rules(db, current_user.id, camera_id, event_type)
    return [
        SecurityRuleResponse(
            id=r.id,
            user_id=r.user_id,
            camera_id=r.camera_id,
            camera_name=r.camera.name if r.camera else None,
            zone_id=r.zone_id,
            zone_name=r.zone.name if r.zone else None,
            name=r.name,
            description=r.description,
            event_type=r.event_type,
            severity=r.severity,
            is_enabled=r.is_enabled,
            threshold_value=r.threshold_value,
            threshold_seconds=r.threshold_seconds,
            minimum_confidence=r.minimum_confidence,
            class_filters=r.class_filters,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rules
    ]


@router.post(
    "/api/security-rules",
    response_model=SecurityRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new security rule",
)
def create_rule(
    data: SecurityRuleCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityRuleResponse:
    r = security_event_service.create_security_rule(db, current_user.id, data)
    return SecurityRuleResponse(
        id=r.id,
        user_id=r.user_id,
        camera_id=r.camera_id,
        camera_name=r.camera.name if r.camera else None,
        zone_id=r.zone_id,
        zone_name=r.zone.name if r.zone else None,
        name=r.name,
        description=r.description,
        event_type=r.event_type,
        severity=r.severity,
        is_enabled=r.is_enabled,
        threshold_value=r.threshold_value,
        threshold_seconds=r.threshold_seconds,
        minimum_confidence=r.minimum_confidence,
        class_filters=r.class_filters,
        created_at=r.created_at.isoformat(),
        updated_at=r.updated_at.isoformat(),
    )


@router.get(
    "/api/security-rules/{rule_id}",
    response_model=SecurityRuleResponse,
    summary="Retrieve a security rule by ID",
)
def get_rule(
    rule_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityRuleResponse:
    r = security_event_service.get_security_rule_by_id(db, current_user.id, rule_id)
    return SecurityRuleResponse(
        id=r.id,
        user_id=r.user_id,
        camera_id=r.camera_id,
        camera_name=r.camera.name if r.camera else None,
        zone_id=r.zone_id,
        zone_name=r.zone.name if r.zone else None,
        name=r.name,
        description=r.description,
        event_type=r.event_type,
        severity=r.severity,
        is_enabled=r.is_enabled,
        threshold_value=r.threshold_value,
        threshold_seconds=r.threshold_seconds,
        minimum_confidence=r.minimum_confidence,
        class_filters=r.class_filters,
        created_at=r.created_at.isoformat(),
        updated_at=r.updated_at.isoformat(),
    )


@router.put(
    "/api/security-rules/{rule_id}",
    response_model=SecurityRuleResponse,
    summary="Update an existing security rule",
)
def update_rule(
    rule_id: str,
    data: SecurityRuleUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityRuleResponse:
    r = security_event_service.update_security_rule(db, current_user.id, rule_id, data)
    return SecurityRuleResponse(
        id=r.id,
        user_id=r.user_id,
        camera_id=r.camera_id,
        camera_name=r.camera.name if r.camera else None,
        zone_id=r.zone_id,
        zone_name=r.zone.name if r.zone else None,
        name=r.name,
        description=r.description,
        event_type=r.event_type,
        severity=r.severity,
        is_enabled=r.is_enabled,
        threshold_value=r.threshold_value,
        threshold_seconds=r.threshold_seconds,
        minimum_confidence=r.minimum_confidence,
        class_filters=r.class_filters,
        created_at=r.created_at.isoformat(),
        updated_at=r.updated_at.isoformat(),
    )


@router.patch(
    "/api/security-rules/{rule_id}/status",
    response_model=SecurityRuleResponse,
    summary="Quick toggle a security rule enabled status",
)
def toggle_rule_status(
    rule_id: str,
    is_enabled: bool = Query(..., description="Target enabled state"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityRuleResponse:
    r = security_event_service.update_security_rule(
        db, current_user.id, rule_id, SecurityRuleUpdate(is_enabled=is_enabled)
    )
    return SecurityRuleResponse(
        id=r.id,
        user_id=r.user_id,
        camera_id=r.camera_id,
        camera_name=r.camera.name if r.camera else None,
        zone_id=r.zone_id,
        zone_name=r.zone.name if r.zone else None,
        name=r.name,
        description=r.description,
        event_type=r.event_type,
        severity=r.severity,
        is_enabled=r.is_enabled,
        threshold_value=r.threshold_value,
        threshold_seconds=r.threshold_seconds,
        minimum_confidence=r.minimum_confidence,
        class_filters=r.class_filters,
        created_at=r.created_at.isoformat(),
        updated_at=r.updated_at.isoformat(),
    )


@router.delete(
    "/api/security-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a security rule",
)
def delete_rule(
    rule_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    security_event_service.delete_security_rule(db, current_user.id, rule_id)


# ─── Security Events ─────────────────────────────────────────────────────────

@router.get(
    "/api/security-events",
    response_model=List[SecurityEventResponse],
    summary="List security events with filtering",
)
def list_events(
    event_type: Optional[SecurityEventType] = Query(None, description="Filter by event type"),
    severity: Optional[SecurityEventSeverity] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, ACKNOWLEDGED, etc."),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    analysis_job_id: Optional[str] = Query(None, description="Filter by analysis job ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SecurityEventResponse]:
    return security_event_service.get_security_events(
        db,
        user_id=current_user.id,
        event_type=event_type,
        severity=severity,
        status_filter=status,
        camera_id=camera_id,
        analysis_job_id=analysis_job_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/security-events/metrics",
    response_model=EventMetricsResponse,
    summary="Aggregated security event metrics for SOC dashboard",
)
def get_metrics(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventMetricsResponse:
    return security_event_service.get_event_metrics(db, current_user.id)


@router.get(
    "/api/security-events/{event_id}",
    response_model=SecurityEventResponse,
    summary="Retrieve detailed security event by ID",
)
def get_event(
    event_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityEventResponse:
    return security_event_service.get_security_event_by_id(db, current_user.id, event_id)


@router.patch(
    "/api/security-events/{event_id}/status",
    response_model=SecurityEventResponse,
    summary="Update security event workflow status",
)
def update_event_status_endpoint(
    event_id: str,
    data: SecurityEventStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityEventResponse:
    return security_event_service.update_event_status(
        db, current_user.id, event_id, data.status
    )
