import os
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.core.security import decode_access_token
from app.schemas.detection import DetectionResponse, DetectionSummary
from app.schemas.tracking import (
    TrackDetailResponse,
    TrackedObjectResponse,
    TrackingSummaryResponse,
)
from app.schemas.user import UserResponse
from app.schemas.video_analysis import (
    ActiveJobsCountResponse,
    AnalysisJobCreateResponse,
    AnalysisJobResponse,
    AnalysisResultResponse,
)
from app.services import tracking_service
from app.services.auth_service import get_user_by_id
from app.services.detection_service import (
    get_annotated_frame_path_for_serving,
    get_detection_summary,
    get_frame_detections,
)
from app.services.video_analysis_service import (
    cancel_job,
    create_analysis_job,
    get_active_jobs_count,
    get_frame_path_for_serving,
    get_job_by_id,
    get_job_results_with_urls,
    get_user_jobs,
    run_analysis_pipeline_background,
    save_uploaded_file,
)

router = APIRouter(prefix="/api/video-analysis", tags=["Video Analysis"])

optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_for_media(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme),
    token_param: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Flexible auth dependency for serving media (frames/thumbnails).
    Supports:
      1. Standard Authorization: Bearer <token>
      2. ?token=<jwt> query parameter (for direct <img> tags)
      3. sentinel_token cookie
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif token_param:
        token = token_param
    elif "sentinel_token" in request.cookies:
        token = request.cookies.get("sentinel_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse.model_validate(user)


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=AnalysisJobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload video and queue background analysis",
)
@router.post(
    "/upload/",
    response_model=AnalysisJobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisJobCreateResponse:
    """
    Securely uploads a surveillance video file, creates a database job record,
    and queues background OpenCV processing.
    """
    saved_path, original_filename = save_uploaded_file(file, current_user.id)
    job = create_analysis_job(
        db=db,
        user_id=current_user.id,
        source_path=saved_path,
        original_filename=original_filename,
        camera_id=camera_id,
    )

    # Queue non-blocking processing
    background_tasks.add_task(run_analysis_pipeline_background, job.id)

    return AnalysisJobCreateResponse(
        id=job.id,
        status=job.status,
        original_filename=job.original_filename,
        progress=job.progress,
    )


@router.get(
    "",
    response_model=List[AnalysisJobResponse],
    summary="List analysis jobs for current user",
)
@router.get(
    "/",
    response_model=List[AnalysisJobResponse],
    include_in_schema=False,
)
def list_analysis_jobs(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AnalysisJobResponse]:
    """Retrieve all video analysis jobs belonging to the authenticated user."""
    jobs = get_user_jobs(db, current_user.id)
    return [AnalysisJobResponse.model_validate(j) for j in jobs]


@router.get(
    "/active-count",
    response_model=ActiveJobsCountResponse,
    summary="Get count of active processing jobs",
)
def get_active_jobs_metrics(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActiveJobsCountResponse:
    """Returns number of active (queued + processing) jobs for the SOC dashboard."""
    counts = get_active_jobs_count(db, current_user.id)
    return ActiveJobsCountResponse(**counts)


@router.get(
    "/{job_id}",
    response_model=AnalysisJobResponse,
    summary="Get video analysis job details",
)
def get_single_analysis_job(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisJobResponse:
    """Retrieve detailed metadata and progress for a single analysis job."""
    job = get_job_by_id(db, job_id, current_user.id)
    return AnalysisJobResponse.model_validate(job)


@router.get(
    "/{job_id}/results",
    response_model=List[AnalysisResultResponse],
    summary="Get sampled frame results for an analysis job",
)
def get_analysis_results(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AnalysisResultResponse]:
    """Retrieve all representative sampled frames and timestamps for a completed job."""
    results = get_job_results_with_urls(db, job_id, current_user.id)
    return [AnalysisResultResponse(**r) for r in results]


@router.get(
    "/{job_id}/frames/{filename}",
    summary="Serve an extracted frame or thumbnail image",
)
def serve_extracted_frame(
    job_id: str,
    filename: str,
    current_user: UserResponse = Depends(get_current_user_for_media),
    db: Session = Depends(get_db),
):
    """
    Securely stream an extracted frame JPEG image.
    Verifies user ownership of the job and prevents path traversal.
    """
    file_path = get_frame_path_for_serving(db, job_id, filename, current_user.id)
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=filename,
    )


@router.patch(
    "/{job_id}/cancel",
    response_model=AnalysisJobResponse,
    summary="Cancel an active analysis job",
)
def cancel_analysis_job(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisJobResponse:
    """Cancel a queued or currently processing video analysis job."""
    job = cancel_job(db, job_id, current_user.id)
    return AnalysisJobResponse.model_validate(job)


# ─── Phase 4 Detection Endpoints ─────────────────────────────────────────────


@router.get(
    "/{job_id}/detections/summary",
    response_model=DetectionSummary,
    summary="Get aggregated object detection summary and statistics for a job",
)
def get_job_detection_summary(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DetectionSummary:
    """
    Returns aggregated detection statistics including total counts, frames with detections,
    unique classes, average confidence, and class breakdown for the specified job.
    """
    return get_detection_summary(db, job_id, current_user.id)


@router.get(
    "/{job_id}/results/{result_id}/detections",
    response_model=List[DetectionResponse],
    summary="Get all object detections for a specific sampled frame",
)
def get_sampled_frame_detections(
    job_id: str,
    result_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[DetectionResponse]:
    """
    Retrieves all detected objects and bounding box coordinates for a specific frame.
    """
    return get_frame_detections(db, job_id, result_id, current_user.id)


@router.get(
    "/{job_id}/annotated/{filename}",
    summary="Serve an AI-annotated frame image",
)
def serve_annotated_frame(
    job_id: str,
    filename: str,
    current_user: UserResponse = Depends(get_current_user_for_media),
    db: Session = Depends(get_db),
):
    """
    Securely stream an AI-annotated frame JPEG image with drawn bounding boxes.
    Verifies user ownership of the job and prevents path traversal.
    """
    file_path = get_annotated_frame_path_for_serving(db, job_id, filename, current_user.id)
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=filename,
    )


# ── Phase 5: Object Tracking & Temporal Intelligence ──────────────────────────

@router.get(
    "/{job_id}/tracking/summary",
    response_model=TrackingSummaryResponse,
    summary="Retrieve object tracking summary statistics",
)
def get_tracking_summary(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackingSummaryResponse:
    """
    Returns aggregated tracking metrics for a completed analysis job:
    total unique objects, class breakdowns, duration statistics, and most frequent class.
    """
    summary = tracking_service.get_tracking_summary(db, job_id, current_user.id)
    return TrackingSummaryResponse(**summary)


@router.get(
    "/{job_id}/tracks",
    response_model=List[TrackedObjectResponse],
    summary="List tracked objects for an analysis job",
)
def list_tracked_objects(
    job_id: str,
    class_name: Optional[str] = Query(None, description="Filter by object class name"),
    min_duration: Optional[float] = Query(None, description="Minimum track duration in seconds"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TrackedObjectResponse]:
    """
    Returns all unique tracked objects for a job, with optional class name and duration filters.
    Each tracked object includes its lifecycle window, observation count, and confidence metrics.

    Note: Track IDs are unique only within a single analysis job.
    """
    tracks = tracking_service.get_tracked_objects(
        db, job_id, current_user.id,
        class_name=class_name,
        min_duration=min_duration,
    )
    result = []
    for t in tracks:
        result.append(TrackedObjectResponse(
            id=t.id,
            track_id=t.track_id,
            class_id=t.class_id,
            class_name=t.class_name,
            first_seen_timestamp=round(t.first_seen_timestamp, 3),
            last_seen_timestamp=round(t.last_seen_timestamp, 3),
            duration_seconds=round(t.last_seen_timestamp - t.first_seen_timestamp, 2),
            first_seen_frame=t.first_seen_frame,
            last_seen_frame=t.last_seen_frame,
            total_frames=t.total_frames,
            average_confidence=round(t.average_confidence, 4),
            max_confidence=round(t.max_confidence, 4),
        ))
    return result


@router.get(
    "/{job_id}/tracks/{track_id}",
    response_model=TrackDetailResponse,
    summary="Retrieve full track detail including trajectory",
)
def get_track_detail(
    job_id: str,
    track_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackDetailResponse:
    """
    Returns complete temporal metadata, movement metrics, and trajectory points for a tracked object.
    Displacement and trajectory distance are measured in frame pixel coordinates.

    Note: Track IDs are unique only within a single analysis job.
    """
    detail = tracking_service.get_track_detail(db, job_id, track_id, current_user.id)
    from app.schemas.tracking import TrackPointResponse
    trajectory_responses = [
        TrackPointResponse(**pt) for pt in detail["trajectory"]
    ]
    return TrackDetailResponse(
        id=detail["id"],
        track_id=detail["track_id"],
        class_id=detail["class_id"],
        class_name=detail["class_name"],
        first_seen_timestamp=detail["first_seen_timestamp"],
        last_seen_timestamp=detail["last_seen_timestamp"],
        duration_seconds=detail["duration_seconds"],
        first_seen_frame=detail["first_seen_frame"],
        last_seen_frame=detail["last_seen_frame"],
        total_frames=detail["total_frames"],
        average_confidence=detail["average_confidence"],
        max_confidence=detail["max_confidence"],
        displacement_pixels=detail["displacement_pixels"],
        trajectory_distance_pixels=detail["trajectory_distance_pixels"],
        trajectory=trajectory_responses,
    )


@router.get(
    "/{job_id}/events",
    response_model=List[dict],
    summary="Retrieve security events detected for a specific analysis job",
)
def get_job_security_events(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Convenience route for the Analysis Detail UI to retrieve all security events
    triggered during this analysis run.
    """
    from app.services import security_event_service
    from app.schemas.security_event import SecurityEventResponse
    events: list[SecurityEventResponse] = security_event_service.get_security_events(
        db, user_id=current_user.id, analysis_job_id=job_id, limit=100
    )
    return [ev.model_dump() for ev in events]


