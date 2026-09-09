import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, JSON, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ZoneType(str, enum.Enum):
    """Type of security zone."""
    RESTRICTED = "RESTRICTED"
    CROWD = "CROWD"
    MONITORING = "MONITORING"


class SecurityZone(Base):
    """
    SQLAlchemy model representing a geometric security zone.
    Coordinates are stored as a JSON list of normalized points:
    [{"x": 0.2, "y": 0.3}, ...] where 0.0 <= x, y <= 1.0.
    """
    __tablename__ = "security_zones"

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
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    zone_type = Column(
        Enum(ZoneType),
        default=ZoneType.RESTRICTED,
        nullable=False,
    )
    # JSON list of dicts: [{"x": float, "y": float}, ...]
    coordinates = Column(JSON, nullable=False)
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

    # Relationships
    user = relationship("User", back_populates="security_zones")
    camera = relationship("Camera", back_populates="security_zones")
    rules = relationship(
        "SecurityRule",
        back_populates="zone",
        cascade="all, delete-orphan",
    )
