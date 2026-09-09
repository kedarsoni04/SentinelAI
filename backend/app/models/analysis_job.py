import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Lifecycle status of a video analysis job."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AnalysisJob(Base):
    """
    SQLAlchemy model representing a video analysis job.

    Tracks video processing metadata, sampling stats, progress (0-100),
    and links to individual extracted frame results.
    """
    __tablename__ = "analysis_jobs"

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
    camera_id = Column(
        String(36),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type = Column(String(50), default="VIDEO_FILE", nullable=False)
    source_path = Column(String(1024), nullable=False)
    original_filename = Column(String(255), nullable=False)
    status = Column(
        Enum(JobStatus),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )
    progress = Column(Integer, default=0, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    frame_count = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    sampled_frames = Column(Integer, default=0, nullable=False)
    processed_frames = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    error_message = Column(String(1024), nullable=True)

    # Relationships
    user = relationship("User", back_populates="analysis_jobs")
    camera = relationship("Camera", back_populates="analysis_jobs")
    results = relationship(
        "AnalysisResult",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="AnalysisResult.frame_index",
    )
    tracked_objects = relationship(
        "TrackedObject",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="TrackedObject.track_id.asc()",
    )
    security_events = relationship(
        "SecurityEvent",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="SecurityEvent.start_timestamp.asc()",
    )
    incident_reports = relationship(
        "IncidentReport",
        back_populates="job",
        cascade="all, delete-orphan",
    )
