from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# ─── Request Schemas ────────────────────────────────────────────────────────


class UserRegister(BaseModel):
    """Schema for user registration requests."""

    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()


class UserLogin(BaseModel):
    """Schema for user login requests."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


# ─── Response Schemas ────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """
    Safe user representation for API responses.
    Never includes password_hash or internal fields.
    """

    id: str
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
