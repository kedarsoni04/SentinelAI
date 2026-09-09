import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class IncidentReportStatus(str, enum.Enum):
    """Lifecycle status of an AI-generated incident report."""
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IncidentOperationalStatus(str, enum.Enum):
    """Operational / workflow status of an incident (Phase 9)."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentReport(Base):
    """
    SQLAlchemy model representing an AI-generated incident intelligence report.

    Stores structured AI analysis: summary, event timeline, risk assessment,
    and recommended human review actions. All AI processing is backend-only.
    No raw frames, coordinates, or PII are stored here.
    """
    __tablename__ = "incident_reports"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_job_id = Column(
        String(36),
        ForeignKey("analysis_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    camera_id = Column(
        String(36),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Which security event IDs were included in the context
    event_ids_json = Column(JSON, nullable=False, default=list)

    # AI provider metadata
    ai_provider = Column(String(50), nullable=False, default="mock")
    ai_model = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)

    # AI-generated content
    summary = Column(Text, nullable=True)
    timeline_json = Column(JSON, nullable=True)       # List[{timestamp_label, event_type, description}]
    risk_level = Column(String(20), nullable=True)    # LOW / MEDIUM / HIGH / CRITICAL
    risk_explanation = Column(Text, nullable=True)
    recommendations_json = Column(JSON, nullable=True)  # List[str]
    disclaimer = Column(Text, nullable=True)

    # Report lifecycle
    status = Column(
        String(20),
        default=IncidentReportStatus.GENERATING,
        nullable=False,
        index=True,
    )
    error_message = Column(String(1024), nullable=True)

    # Incident operational lifecycle (Phase 9)
    incident_status = Column(
        String(20),
        default=IncidentOperationalStatus.OPEN,
        nullable=False,
        index=True,
    )
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="incident_reports")
    job = relationship("AnalysisJob", back_populates="incident_reports")
    camera = relationship("Camera", back_populates="incident_reports")
