import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles for role-based access control."""
    ADMIN = "ADMIN"
    SECURITY_OPERATOR = "SECURITY_OPERATOR"
    VIEWER = "VIEWER"


class User(Base):
    """
    SQLAlchemy User model.

    Stores authentication credentials and role information.
    Password hashes are NEVER returned in API responses.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.SECURITY_OPERATOR,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    analysis_jobs = relationship(
        "AnalysisJob",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    security_zones = relationship(
        "SecurityZone",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    security_rules = relationship(
        "SecurityRule",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    incident_reports = relationship(
        "IncidentReport",
        back_populates="user",
        cascade="all, delete-orphan",
    )
