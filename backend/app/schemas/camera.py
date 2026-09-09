from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.camera import CameraSourceType, CameraStatus


# ─── Request Schemas ─────────────────────────────────────────────────────────


class CameraCreate(BaseModel):
    """Schema for creating a new camera."""

    name: str = Field(..., min_length=1, max_length=255, description="Human-readable camera name")
    location: str = Field(..., min_length=1, max_length=255, description="Physical camera location")
    stream_url: Optional[str] = Field(None, max_length=1024, description="Optional stream URL (RTSP, HTTP, etc.)")
    source_type: CameraSourceType = Field(..., description="Camera input source type")
    is_enabled: bool = Field(True, description="Whether the camera is active")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Camera name cannot be blank")
        return v.strip()

    @field_validator("location")
    @classmethod
    def location_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Camera location cannot be blank")
        return v.strip()

    @field_validator("stream_url")
    @classmethod
    def validate_stream_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        # Basic URL structure validation — do NOT attempt connection in Phase 2
        if not (v.startswith("rtsp://") or v.startswith("http://") or
                v.startswith("https://") or v.startswith("rtsps://")):
            raise ValueError(
                "Stream URL must start with rtsp://, rtsps://, http://, or https://"
            )
        return v


class CameraUpdate(BaseModel):
    """Schema for updating a camera — all fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    stream_url: Optional[str] = Field(None, max_length=1024)
    source_type: Optional[CameraSourceType] = None
    status: Optional[CameraStatus] = None
    is_enabled: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Camera name cannot be blank")
        return v.strip() if v else v

    @field_validator("location")
    @classmethod
    def location_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Camera location cannot be blank")
        return v.strip() if v else v

    @field_validator("stream_url")
    @classmethod
    def validate_stream_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not (v.startswith("rtsp://") or v.startswith("http://") or
                v.startswith("https://") or v.startswith("rtsps://")):
            raise ValueError(
                "Stream URL must start with rtsp://, rtsps://, http://, or https://"
            )
        return v


class CameraStatusUpdate(BaseModel):
    """Schema for the enable/disable endpoint."""

    is_enabled: bool = Field(..., description="Set to true to enable, false to disable")


# ─── Response Schema ──────────────────────────────────────────────────────────


class CameraResponse(BaseModel):
    """
    Safe camera representation for API responses.
    Returns all configuration fields needed by the frontend.
    """

    id: str
    name: str
    location: str
    stream_url: Optional[str]
    source_type: CameraSourceType
    status: CameraStatus
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime]

    model_config = {"from_attributes": True}
