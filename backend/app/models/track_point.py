import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrackPoint(Base):
    """
    SQLAlchemy model representing an individual temporal observation along an object's trajectory.
    Stores bounding box coordinates, derived center coordinates, observation confidence,
    and references to the parent tracked object and analysis frame.
    """
    __tablename__ = "track_points"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    tracked_object_id = Column(
        String(36),
        ForeignKey("tracked_objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_result_id = Column(
        String(36),
        ForeignKey("analysis_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    frame_index = Column(Integer, nullable=False, index=True)
    timestamp_seconds = Column(Float, nullable=False)
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tracked_object = relationship("TrackedObject", back_populates="points")
    analysis_result = relationship("AnalysisResult")
