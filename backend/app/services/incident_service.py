"""
Incident Intelligence Service — Phase 8.

Handles creation, async AI analysis, retrieval, and deletion of IncidentReports.
All AI processing runs in a background thread to avoid blocking the event loop.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.context_builder import IncidentContextBuilder
from app.ai.provider_factory import get_ai_provider
from app.core.database import SessionLocal
from app.models.camera import Camera
from app.models.incident_report import IncidentReport, IncidentReportStatus
from app.schemas.incident import (
    IncidentReportListItem,
    IncidentReportResponse,
)

logger = logging.getLogger("sentinel.services.incident")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _format_report(report: IncidentReport) -> IncidentReportResponse:
    """Convert ORM model to Pydantic response schema."""
    camera_name: Optional[str] = None
    if report.camera:
        camera_name = report.camera.name

    event_ids = report.event_ids_json or []
    return IncidentReportResponse(
        id=report.id,
        user_id=report.user_id,
        analysis_job_id=report.analysis_job_id,
        camera_id=report.camera_id,
        camera_name=camera_name,
        event_ids=event_ids,
        event_count=len(event_ids),
        ai_provider=report.ai_provider,
        ai_model=report.ai_model,
        prompt_tokens=report.prompt_tokens,
        summary=report.summary,
        timeline=report.timeline_json,
        risk_level=report.risk_level,
        risk_explanation=report.risk_explanation,
        recommendations=report.recommendations_json,
        disclaimer=report.disclaimer,
        status=report.status,
        error_message=report.error_message,
        created_at=report.created_at.isoformat() if report.created_at else "",
        updated_at=report.updated_at.isoformat() if report.updated_at else "",
    )


def _format_list_item(report: IncidentReport) -> IncidentReportListItem:
    """Convert ORM model to compact list item schema."""
    camera_name: Optional[str] = None
    if report.camera:
        camera_name = report.camera.name

    event_ids = report.event_ids_json or []
    summary_preview = None
    if report.summary:
        summary_preview = report.summary[:200] + ("…" if len(report.summary) > 200 else "")

    return IncidentReportListItem(
        id=report.id,
        user_id=report.user_id,
        camera_id=report.camera_id,
        camera_name=camera_name,
        event_count=len(event_ids),
        ai_provider=report.ai_provider,
        risk_level=report.risk_level,
        summary_preview=summary_preview,
        status=report.status,
        created_at=report.created_at.isoformat() if report.created_at else "",
    )


# ─── CRUD ────────────────────────────────────────────────────────────────────

def create_incident_report(
    db: Session,
    user_id: str,
    event_ids: List[str],
    job_id: Optional[str] = None,
) -> IncidentReport:
    """
    Insert a new IncidentReport record with GENERATING status.
    Returns immediately — analysis runs as a background task.
    """
    # Determine camera_id from first event if available
    camera_id: Optional[str] = None
    try:
        from app.models.security_event import SecurityEvent
        from app.models.analysis_job import AnalysisJob
        first_event = (
            db.query(SecurityEvent)
            .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
            .filter(
                SecurityEvent.id.in_(event_ids),
                AnalysisJob.user_id == user_id,
            )
            .first()
        )
        if first_event and first_event.camera_id:
            camera_id = first_event.camera_id
    except Exception:
        pass

    # Get provider info without running analysis
    provider = get_ai_provider()

    report = IncidentReport(
        id=str(uuid.uuid4()),
        user_id=user_id,
        analysis_job_id=job_id,
        camera_id=camera_id,
        event_ids_json=list(event_ids),
        ai_provider=provider.provider_name,
        ai_model=provider.model_name,
        status=IncidentReportStatus.GENERATING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    logger.info("Created IncidentReport id=%s for user=%s", report.id, user_id)
    return report


async def run_incident_analysis(report_id: str, user_id: str) -> None:
    """
    Background task: run AI analysis and update the IncidentReport record.

    Uses a fresh DB session (not the request session which may be closed).
    """
    db = SessionLocal()
    try:
        report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
        if not report:
            logger.error("run_incident_analysis: report %s not found", report_id)
            return

        # Build context
        builder = IncidentContextBuilder(db, user_id)
        context = builder.build(
            report_id=report_id,
            event_ids=report.event_ids_json or [],
            job_id=report.analysis_job_id,
        )

        # Get provider and run analysis
        provider = get_ai_provider()
        logger.info(
            "run_incident_analysis: report=%s provider=%s",
            report_id,
            provider.provider_name,
        )

        try:
            result = await provider.generate_incident_analysis(context)

            report.summary = result.summary
            report.timeline_json = result.timeline
            report.risk_level = result.risk_level
            report.risk_explanation = result.risk_explanation
            report.recommendations_json = result.recommendations
            report.disclaimer = result.disclaimer
            report.ai_provider = result.ai_provider
            report.ai_model = result.ai_model
            report.prompt_tokens = result.prompt_tokens
            report.status = IncidentReportStatus.COMPLETED

        except Exception as exc:
            logger.error("AI analysis failed for report %s: %s", report_id, exc)
            report.status = IncidentReportStatus.FAILED
            report.error_message = str(exc)[:1000]

        db.commit()
        logger.info("run_incident_analysis: finished report=%s status=%s", report_id, report.status)

    except Exception as exc:
        logger.error("Unexpected error in run_incident_analysis for %s: %s", report_id, exc)
        try:
            report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
            if report:
                report.status = IncidentReportStatus.FAILED
                report.error_message = "Internal analysis error."
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def get_user_incident_reports(
    db: Session,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[IncidentReportListItem]:
    """Retrieve paginated list of incident reports for a user."""
    reports = (
        db.query(IncidentReport)
        .filter(IncidentReport.user_id == user_id)
        .order_by(IncidentReport.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_format_list_item(r) for r in reports]


def get_incident_report(
    db: Session,
    report_id: str,
    user_id: str,
) -> IncidentReportResponse:
    """Retrieve a single incident report with ownership check."""
    report = (
        db.query(IncidentReport)
        .filter(
            IncidentReport.id == report_id,
            IncidentReport.user_id == user_id,
        )
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident report '{report_id}' not found.",
        )
    return _format_report(report)


def delete_incident_report(
    db: Session,
    report_id: str,
    user_id: str,
) -> None:
    """Delete an incident report with ownership check."""
    report = (
        db.query(IncidentReport)
        .filter(
            IncidentReport.id == report_id,
            IncidentReport.user_id == user_id,
        )
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident report '{report_id}' not found.",
        )
    db.delete(report)
    db.commit()
    logger.info("Deleted IncidentReport id=%s by user=%s", report_id, user_id)
