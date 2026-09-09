import datetime
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import SessionLocal, get_db
from app.core.security import decode_access_token
from app.core.websocket_manager import get_connection_manager
from app.models.analysis_job import AnalysisJob
from app.models.analysis_result import AnalysisResult
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.realtime_service import RealtimeStatus, get_realtime_session_manager

logger = logging.getLogger("sentinel.api.routes.realtime")

router = APIRouter(tags=["Real-Time Monitoring & SOC Operations"])


@router.post("/api/video-analysis/{job_id}/realtime/start", summary="Start Real-Time Video Monitoring")
def start_realtime_monitoring(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Start a real-time monitoring session for an existing analysis job.
    Evaluates YOLO detection, ByteTrack tracking, and Security Rules frame-by-frame.
    Streams events to connected WebSockets in real time.
    """
    manager = get_realtime_session_manager()
    session = manager.start_session(job_id=job_id, user_id=current_user.id, db=db)
    return session.to_dict()


@router.post("/api/video-analysis/{job_id}/realtime/stop", summary="Stop Real-Time Video Monitoring")
def stop_realtime_monitoring(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Signal an active real-time monitoring session to safely stop.
    Finalizes security events and releases OpenCV and tracker resources.
    """
    manager = get_realtime_session_manager()
    session = manager.stop_session(job_id=job_id, user_id=current_user.id)
    return session.to_dict()


@router.get("/api/video-analysis/{job_id}/realtime/status", summary="Get Real-Time Monitoring Session Status")
def get_realtime_monitoring_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get current telemetry and execution status for a real-time monitoring session.
    Returns live FPS, current timestamp, active tracks count, and events detected.
    """
    manager = get_realtime_session_manager()
    status_data = manager.get_session_status(job_id=job_id, user_id=current_user.id)

    if status_data:
        return status_data

    # Fallback to database status if session is not active in memory
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found or access denied.",
        )

    # Return standard status representation from DB
    return {
        "job_id": job.id,
        "user_id": job.user_id,
        "camera_id": job.camera_id,
        "camera_name": None,
        "status": RealtimeStatus.COMPLETED if job.status == "COMPLETED" else RealtimeStatus.STOPPED,
        "start_time": job.started_at.isoformat() if job.started_at else None,
        "end_time": job.completed_at.isoformat() if job.completed_at else None,
        "current_timestamp": round(job.duration_seconds or 0.0, 2),
        "frames_processed": job.processed_frames or 0,
        "processing_fps": round(job.fps or 0.0, 1),
        "active_tracks": 0,
        "active_tracks_list": [],
        "events_detected": len(job.security_events) if job.security_events else 0,
        "last_heartbeat": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "latest_frame_index": None,
        "error_message": job.error_message,
    }


@router.get("/api/video-analysis/{job_id}/realtime/frame", summary="Get Latest Processed / Annotated Frame")
def get_latest_realtime_frame(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Serve the latest processed or annotated frame from an active or finished monitoring session.
    """
    # Verify job ownership
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found or access denied.",
        )

    # Check active session first
    manager = get_realtime_session_manager()
    session = manager.get_session(job_id)
    if session and session.user_id == current_user.id:
        frame_path = session.latest_annotated_frame_path or session.latest_frame_path
        if frame_path and os.path.exists(frame_path):
            return FileResponse(frame_path, media_type="image/jpeg")

    # Fallback to latest AnalysisResult in database
    latest_result = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.analysis_job_id == job_id)
        .order_by(AnalysisResult.frame_index.desc())
        .first()
    )
    if latest_result:
        fpath = latest_result.annotated_frame_path or latest_result.frame_path
        if fpath and os.path.exists(fpath):
            return FileResponse(fpath, media_type="image/jpeg")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No processed frames available for this job yet.",
    )


@router.get("/api/video-analysis/realtime/active", summary="List Active Real-Time Monitoring Sessions")
def list_active_monitoring_sessions(
    current_user: UserResponse = Depends(get_current_user),
):
    """List all currently active or starting monitoring sessions for the authenticated operator."""
    manager = get_realtime_session_manager()
    return manager.get_active_sessions_for_user(current_user.id)


# ─── Authenticated WebSocket Stream ──────────────────────────────────────────

@router.websocket("/api/ws/analysis/{job_id}")
async def websocket_analysis_endpoint(
    websocket: WebSocket,
    job_id: str,
    token: Optional[str] = Query(default=None),
):
    """
    Authenticated WebSocket endpoint for real-time video analysis & SOC security events.
    Verifies JWT token and analysis job ownership before granting subscription.
    """
    # 1. Extract token from query param or headers
    auth_token = token
    if not auth_token:
        # Check Sec-WebSocket-Protocol or Authorization header
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            auth_token = auth_header[7:].strip()

    if not auth_token:
        logger.warning(f"WebSocket rejected for job {job_id}: missing auth token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Decode and validate token
    user_id = decode_access_token(auth_token)
    if not user_id:
        logger.warning(f"WebSocket rejected for job {job_id}: invalid or expired token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3. Validate user existence and job ownership
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"WebSocket rejected for job {job_id}: user {user_id} not found.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        job = (
            db.query(AnalysisJob)
            .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
            .first()
        )
        if not job:
            logger.warning(f"WebSocket rejected: user {user_id} does not own job {job_id}.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()

    # 4. Accept connection and register with ConnectionManager
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket, job_id, user_id)

    # 5. Send initial status update upon connection
    session_manager = get_realtime_session_manager()
    initial_status = session_manager.get_session_status(job_id, user_id) or {
        "job_id": job_id,
        "status": RealtimeStatus.STOPPED,
        "message": "Connected to real-time surveillance stream",
    }
    await websocket.send_json({
        "type": "status_update",
        "data": initial_status,
        "job_id": job_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

    # 6. Keep-alive receive loop
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client ping or heartbeat messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error for job {job_id}: {e}")
        connection_manager.disconnect(websocket)
