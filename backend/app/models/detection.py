import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Detection(Base):
    """
    SQLAlchemy model representing an individual object detection within an extracted frame.
    Stores numerical class ID, human-readable class name, confidence score, and bounding box coordinates.
    """
    __tablename__ = "detections"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    analysis_result_id = Column(
        String(36),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    track_id = Column(Integer, nullable=True, index=True)
    tracked_object_id = Column(
        String(36),
        ForeignKey("tracked_objects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    result = relationship("AnalysisResult", back_populates="detections")
    tracked_object = relationship("TrackedObject", back_populates="detections")
