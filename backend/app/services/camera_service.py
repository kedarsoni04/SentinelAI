from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.camera import Camera, CameraStatus
from app.schemas.camera import CameraCreate, CameraResponse, CameraStatusUpdate, CameraUpdate


def get_cameras(db: Session) -> List[CameraResponse]:
    """
    Retrieve all cameras ordered by creation date (newest first).
    """
    cameras = db.query(Camera).order_by(Camera.created_at.desc()).all()
    return [CameraResponse.model_validate(c) for c in cameras]


def get_camera(db: Session, camera_id: str) -> CameraResponse:
    """
    Retrieve a single camera by ID.

    Raises:
        404 NOT FOUND — if the camera does not exist.
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found",
        )
    return CameraResponse.model_validate(camera)


def create_camera(db: Session, data: CameraCreate) -> CameraResponse:
    """
    Create a new camera configuration.
    """
    camera = Camera(
        name=data.name,
        location=data.location,
        stream_url=data.stream_url,
        source_type=data.source_type,
        status=CameraStatus.UNKNOWN,  # Phase 2: no live connectivity check
        is_enabled=data.is_enabled,
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return CameraResponse.model_validate(camera)


def update_camera(db: Session, camera_id: str, data: CameraUpdate) -> CameraResponse:
    """
    Update camera configuration fields.

    Only provided (non-None) fields are updated.
    updated_at is handled by SQLAlchemy's onupdate.

    Raises:
        404 NOT FOUND — if the camera does not exist.
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    # Explicitly set updated_at for SQLite compatibility
    # (SQLite's onupdate may not fire without a flush trigger on some versions)
    from datetime import datetime, timezone
    camera.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(camera)
    return CameraResponse.model_validate(camera)


def delete_camera(db: Session, camera_id: str) -> dict:
    """
    Delete a camera configuration permanently.

    Raises:
        404 NOT FOUND — if the camera does not exist.
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found",
        )

    camera_name = camera.name
    db.delete(camera)
    db.commit()
    return {"message": f"Camera '{camera_name}' has been removed successfully"}


def update_camera_status(db: Session, camera_id: str, data: CameraStatusUpdate) -> CameraResponse:
    """
    Enable or disable a camera without deleting its configuration.

    Raises:
        404 NOT FOUND — if the camera does not exist.
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found",
        )

    camera.is_enabled = data.is_enabled

    from datetime import datetime, timezone
    camera.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(camera)
    return CameraResponse.model_validate(camera)


def get_enabled_camera_count(db: Session) -> int:
    """Return the count of enabled cameras. Used by dashboard metrics."""
    return db.query(func.count(Camera.id)).filter(Camera.is_enabled == True).scalar() or 0
