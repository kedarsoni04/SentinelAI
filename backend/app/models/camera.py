import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CameraSourceType(str, enum.Enum):
    """Source type for camera input."""
    WEBCAM = "WEBCAM"
    RTSP = "RTSP"
    HTTP_STREAM = "HTTP_STREAM"
    VIDEO_FILE = "VIDEO_FILE"


class CameraStatus(str, enum.Enum):
    """Operational status of a camera."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class Camera(Base):
    """
    SQLAlchemy Camera model.

    Represents a configured surveillance camera source.
    Phase 2: Configuration and management only.
    Live connectivity checking is not implemented until Phase 3.
    """
    __tablename__ = "cameras"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    stream_url = Column(String(1024), nullable=True)
    source_type = Column(
        Enum(CameraSourceType),
        default=CameraSourceType.RTSP,
        nullable=False,
    )
    status = Column(
        Enum(CameraStatus),
        default=CameraStatus.UNKNOWN,
        nullable=False,
    )
    is_enabled = Column(Boolean, default=True, nullable=False)
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
    last_active = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    analysis_jobs = relationship(
        "AnalysisJob",
        back_populates="camera",
    )
    security_zones = relationship(
        "SecurityZone",
        back_populates="camera",
    )
    security_rules = relationship(
        "SecurityRule",
        back_populates="camera",
    )
    security_events = relationship(
        "SecurityEvent",
        back_populates="camera",
    )
    incident_reports = relationship(
        "IncidentReport",
        back_populates="camera",
    )
