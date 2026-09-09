import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrackedObject(Base):
    """
    SQLAlchemy model representing a uniquely tracked entity across time within a single analysis job.
    Maintains persistent track identity, lifecycle window, total sampled observations,
    and confidence metrics.
    """
    __tablename__ = "tracked_objects"

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
    track_id = Column(Integer, nullable=False, index=True)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(50), nullable=False, index=True)
    first_seen_timestamp = Column(Float, nullable=False)
    last_seen_timestamp = Column(Float, nullable=False)
    first_seen_frame = Column(Integer, nullable=False)
    last_seen_frame = Column(Integer, nullable=False)
    total_frames = Column(Integer, nullable=False, default=1)
    average_confidence = Column(Float, nullable=False)
    max_confidence = Column(Float, nullable=False)
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

    __table_args__ = (
        UniqueConstraint("analysis_job_id", "track_id", name="uq_job_track_id"),
    )

    # Relationships
    job = relationship("AnalysisJob", back_populates="tracked_objects")
    points = relationship(
        "TrackPoint",
        back_populates="tracked_object",
        cascade="all, delete-orphan",
        order_by="TrackPoint.frame_index.asc()",
    )
    detections = relationship("Detection", back_populates="tracked_object")
    security_events = relationship("SecurityEvent", back_populates="tracked_object")
