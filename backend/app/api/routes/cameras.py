from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.schemas.camera import (
    CameraCreate,
    CameraResponse,
    CameraStatusUpdate,
    CameraUpdate,
)
from app.schemas.user import UserResponse
from app.services.camera_service import (
    create_camera,
    delete_camera,
    get_camera,
    get_cameras,
    update_camera,
    update_camera_status,
)

router = APIRouter(prefix="/api/cameras", tags=["Camera Management"])


@router.get(
    "",
    response_model=List[CameraResponse],
    summary="List all cameras",
)
def list_cameras(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CameraResponse]:
    """
    Returns all configured cameras ordered by creation date (newest first).
    Requires authentication.
    """
    return get_cameras(db)


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new camera",
)
def add_camera(
    data: CameraCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CameraResponse:
    """
    Configure a new surveillance camera source.
    Does NOT attempt to connect to the stream (Phase 3+).
    Requires authentication.
    """
    return create_camera(db, data)


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Get camera details",
)
def get_camera_by_id(
    camera_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CameraResponse:
    """
    Returns details for a specific camera.
    Returns 404 if the camera does not exist.
    Requires authentication.
    """
    return get_camera(db, camera_id)


@router.put(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Update camera configuration",
)
def update_camera_config(
    camera_id: str,
    data: CameraUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CameraResponse:
    """
    Update one or more camera configuration fields.
    Only provided fields are updated (partial update).
    Returns 404 if the camera does not exist.
    Requires authentication.
    """
    return update_camera(db, camera_id, data)


@router.delete(
    "/{camera_id}",
    summary="Remove a camera",
)
def remove_camera(
    camera_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Permanently removes a camera configuration.
    Returns 404 if the camera does not exist.
    Requires authentication.
    """
    return delete_camera(db, camera_id)


@router.patch(
    "/{camera_id}/status",
    response_model=CameraResponse,
    summary="Enable or disable a camera",
)
def toggle_camera_status(
    camera_id: str,
    data: CameraStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CameraResponse:
    """
    Enable or disable a camera without deleting its configuration.
    Send { "is_enabled": true } to enable, { "is_enabled": false } to disable.
    Returns 404 if the camera does not exist.
    Requires authentication.
    """
    return update_camera_status(db, camera_id, data)
