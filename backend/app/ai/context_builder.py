"""
IncidentContextBuilder — safely assembles IncidentContext from DB data.

Queries security events, camera, zone, and job metadata.
Enforces user ownership before including any data.
Never includes raw frame paths, coordinates, or PII.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.ai.base import EventSummary, IncidentContext
from app.models.analysis_job import AnalysisJob
from app.models.camera import Camera
from app.models.security_event import SecurityEvent
from app.models.security_zone import SecurityZone

logger = logging.getLogger("sentinel.ai.context_builder")


class IncidentContextBuilder:
    """
    Builds a sanitized IncidentContext from database records.

    Only includes events owned by the requesting user.
    All filesystem paths, frame data, and raw coordinates are excluded.
    """

    def __init__(self, db: Session, user_id: str):
        self._db = db
        self._user_id = user_id

    def build(
        self,
        report_id: str,
        event_ids: List[str],
        job_id: Optional[str] = None,
    ) -> IncidentContext:
        """
        Build and return an IncidentContext for the given event IDs.

        Args:
            report_id: The ID of the IncidentReport being generated (for logging).
            event_ids: List of SecurityEvent IDs to include.
            job_id: Optional AnalysisJob ID to pull video metadata from.

        Returns:
            IncidentContext with sanitized metadata only.
        """
        # Fetch events — enforce ownership via analysis_job.user_id
        events = (
            self._db.query(SecurityEvent)
            .join(AnalysisJob, SecurityEvent.analysis_job_id == AnalysisJob.id)
            .filter(
                SecurityEvent.id.in_(event_ids),
                AnalysisJob.user_id == self._user_id,
            )
            .all()
        )

        if not events:
            logger.warning(
                "ContextBuilder: no owned events found for report=%s, event_ids=%s",
                report_id,
                event_ids,
            )

        # Resolve camera metadata from first event with a camera
        camera_name: Optional[str] = None
        camera_location: Optional[str] = None
        first_camera_id = next(
            (e.camera_id for e in events if e.camera_id), None
        )
        if first_camera_id:
            camera = self._db.query(Camera).filter(Camera.id == first_camera_id).first()
            if camera:
                camera_name = camera.name
                camera_location = camera.location

        # Resolve zone names from rule associations
        zone_names = []
        seen_zone_ids = set()
        for evt in events:
            if evt.rule and evt.rule.zone_id and evt.rule.zone_id not in seen_zone_ids:
                seen_zone_ids.add(evt.rule.zone_id)
                zone = self._db.query(SecurityZone).filter(
                    SecurityZone.id == evt.rule.zone_id
                ).first()
                if zone:
                    zone_names.append(zone.name)

        # Resolve job metadata
        job_filename: Optional[str] = None
        job_duration: Optional[float] = None
        if job_id:
            job = self._db.query(AnalysisJob).filter(
                AnalysisJob.id == job_id,
                AnalysisJob.user_id == self._user_id,
            ).first()
            if job:
                job_filename = job.original_filename
                job_duration = job.duration_seconds
        elif events:
            # Fall back to the job from the first event
            first_job_id = events[0].analysis_job_id
            job = self._db.query(AnalysisJob).filter(
                AnalysisJob.id == first_job_id
            ).first()
            if job:
                job_filename = job.original_filename
                job_duration = job.duration_seconds

        # Build EventSummary list (sanitized — no frame paths)
        event_summaries = []
        for evt in sorted(events, key=lambda e: e.start_timestamp):
            event_summaries.append(EventSummary(
                event_id=evt.id,
                event_type=evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type),
                severity=evt.severity.value if hasattr(evt.severity, "value") else str(evt.severity),
                title=evt.title,
                description=evt.description,
                start_timestamp=evt.start_timestamp,
                end_timestamp=evt.end_timestamp,
                duration_seconds=evt.duration_seconds,
                confidence=evt.confidence,
                class_name=evt.class_name,
                rule_name=evt.rule.name if evt.rule else None,
                zone_name=(
                    self._db.query(SecurityZone.name)
                    .filter(SecurityZone.id == evt.rule.zone_id)
                    .scalar()
                    if evt.rule and evt.rule.zone_id
                    else None
                ),
            ))

        # Aggregate counts
        event_type_counts: dict = {}
        severity_counts: dict = {}
        for es in event_summaries:
            event_type_counts[es.event_type] = event_type_counts.get(es.event_type, 0) + 1
            severity_counts[es.severity] = severity_counts.get(es.severity, 0) + 1

        return IncidentContext(
            report_id=report_id,
            camera_name=camera_name,
            camera_location=camera_location,
            zone_names=zone_names,
            job_original_filename=job_filename,
            job_duration_seconds=job_duration,
            events=event_summaries,
            total_events=len(event_summaries),
            event_type_counts=event_type_counts,
            severity_counts=severity_counts,
        )
