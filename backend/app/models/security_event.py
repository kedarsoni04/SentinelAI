import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.security_rule import SecurityEventSeverity, SecurityEventType


class SecurityEventStatus(str, enum.Enum):
    """Operational status of a detected security event."""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class SecurityEvent(Base):
    """
    SQLAlchemy model representing an operational Security Event detected by SentinelAI.
    Captures temporal lifecycle, evidence frame association, contributing track information,
    and structured metadata for SOC operators.
    """
    __tablename__ = "security_events"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    analysis_job_id = Column(
        String(36),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id = Column(
        String(36),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_id = Column(
        String(36),
        ForeignKey("security_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tracked_object_id = Column(
        String(36),
        ForeignKey("tracked_objects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    track_id = Column(Integer, nullable=True)
    class_name = Column(String(100), nullable=True)
    event_type = Column(
        Enum(SecurityEventType),
        nullable=False,
        index=True,
    )
    severity = Column(
        Enum(SecurityEventSeverity),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(SecurityEventStatus),
        default=SecurityEventStatus.OPEN,
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    start_timestamp = Column(Float, nullable=False, index=True)
    end_timestamp = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    evidence_frame_id = Column(
        String(36),
        ForeignKey("analysis_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_json = Column(JSON, nullable=True)
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
    job = relationship("AnalysisJob", back_populates="security_events")
    camera = relationship("Camera", back_populates="security_events")
    rule = relationship("SecurityRule", back_populates="events")
    tracked_object = relationship("TrackedObject", back_populates="security_events")
    evidence_frame = relationship("AnalysisResult", back_populates="security_events")
