"""
Incident Intelligence API Routes — Phase 8.

POST   /api/incidents           — Create report & trigger AI analysis background task
GET    /api/incidents           — List user's incident reports
GET    /api/incidents/{id}      — Get single report (poll until status != GENERATING)
DELETE /api/incidents/{id}      — Delete report
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.schemas.user import UserResponse
from app.schemas.incident import (
    IncidentReportCreateRequest,
    IncidentReportListItem,
    IncidentReportResponse,
)
from app.services.incident_service import (
    create_incident_report,
    delete_incident_report,
    get_incident_report,
    get_user_incident_reports,
    run_incident_analysis,
)

logger = logging.getLogger("sentinel.api.incidents")

router = APIRouter(prefix="/api/incidents", tags=["Incident Intelligence"])


@router.post(
    "",
    response_model=IncidentReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate AI Incident Report",
    description=(
        "Creates a new AI incident report from the given security event IDs "
        "and triggers background AI analysis. Returns immediately with status=GENERATING. "
        "Poll GET /api/incidents/{id} until status becomes COMPLETED or FAILED."
    ),
)
async def create_report(
    body: IncidentReportCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IncidentReportResponse:
    if not body.event_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one event_id is required.",
        )

    report = create_incident_report(
        db=db,
        user_id=current_user.id,
        event_ids=body.event_ids,
        job_id=body.analysis_job_id,
    )

    # Trigger async AI analysis as background task
    background_tasks.add_task(
        run_incident_analysis,
        report_id=report.id,
        user_id=current_user.id,
    )

    logger.info(
        "API: queued incident analysis report=%s for user=%s",
        report.id,
        current_user.id,
    )

    # Return fresh response
    return get_incident_report(db, report.id, current_user.id)


@router.get(
    "",
    response_model=List[IncidentReportListItem],
    summary="List Incident Reports",
    description="Returns paginated list of AI incident reports for the authenticated user.",
)
def list_reports(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> List[IncidentReportListItem]:
    return get_user_incident_reports(db, current_user.id, limit=limit, offset=offset)


@router.get(
    "/{report_id}",
    response_model=IncidentReportResponse,
    summary="Get Incident Report",
    description=(
        "Retrieve a single AI incident report. "
        "If status=GENERATING, poll again in a few seconds."
    ),
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IncidentReportResponse:
    return get_incident_report(db, report_id, current_user.id)


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Incident Report",
    description="Permanently delete an incident report. Requires ownership.",
)
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    delete_incident_report(db, report_id, current_user.id)
