import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisResult(Base):
    """
    SQLAlchemy model representing an extracted frame from a video analysis job.

    Stores frame index, video timestamp, local storage paths (frame and thumbnail),
    resolution, and processing latency. Future phases will link object detections here.
    """
    __tablename__ = "analysis_results"

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
    frame_index = Column(Integer, nullable=False)
    timestamp_seconds = Column(Float, nullable=False)
    frame_path = Column(String(1024), nullable=False)
    thumbnail_path = Column(String(1024), nullable=True)
    annotated_frame_path = Column(String(1024), nullable=True)
    detection_count = Column(Integer, default=0, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    processing_time_ms = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    job = relationship("AnalysisJob", back_populates="results")
    detections = relationship(
        "Detection",
        back_populates="result",
        cascade="all, delete-orphan",
        order_by="Detection.confidence.desc()",
    )
    security_events = relationship(
        "SecurityEvent",
        back_populates="evidence_frame",
    )
