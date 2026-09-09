import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, JSON, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class SecurityEventType(str, enum.Enum):
    """Supported security event types in SentinelAI Phase 6."""
    INTRUSION = "INTRUSION"
    LOITERING = "LOITERING"
    STATIONARY_OBJECT = "STATIONARY_OBJECT"
    CROWD_DENSITY = "CROWD_DENSITY"
    UNUSUAL_MOVEMENT = "UNUSUAL_MOVEMENT"


class SecurityEventSeverity(str, enum.Enum):
    """Operational priority of detected rule conditions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityRule(Base):
    """
    SQLAlchemy model representing a configurable security rule.
    Rules evaluate observable conditions (e.g. zone intrusion, loitering)
    and define thresholds, class filters, and default event severities.
    """
    __tablename__ = "security_rules"

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
    zone_id = Column(
        String(36),
        ForeignKey("security_zones.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    event_type = Column(
        Enum(SecurityEventType),
        nullable=False,
        index=True,
    )
    severity = Column(
        Enum(SecurityEventSeverity),
        default=SecurityEventSeverity.MEDIUM,
        nullable=False,
    )
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Threshold parameters (depending on event_type)
    # - LOITERING: threshold_seconds
    # - STATIONARY_OBJECT: threshold_value (displacement px), threshold_seconds (duration)
    # - CROWD_DENSITY: threshold_value (crowd count)
    # - UNUSUAL_MOVEMENT: threshold_value (speed px/s)
    threshold_value = Column(Float, nullable=True)
    threshold_seconds = Column(Float, nullable=True)
    minimum_confidence = Column(Float, default=0.5, nullable=True)

    # Class filters: e.g. ["person"], ["car", "truck"]
    class_filters = Column(JSON, nullable=True)

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
    user = relationship("User", back_populates="security_rules")
    camera = relationship("Camera", back_populates="security_rules")
    zone = relationship("SecurityZone", back_populates="rules")
    events = relationship(
        "SecurityEvent",
        back_populates="rule",
        cascade="all, delete-orphan",
    )
