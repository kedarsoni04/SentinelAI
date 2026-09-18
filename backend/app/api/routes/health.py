import os
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["System & Health"])

START_TIME = time.time()


@router.get("/api/health", summary="Liveness Probe")
@router.get("/health", summary="Liveness Probe (Direct)")
def health_check() -> Dict[str, Any]:
    """
    Liveness Check:
    Verifies that the backend process is running and able to handle HTTP requests.
    Returns basic service metadata and uptime.
    """
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "healthy",
        "service": "sentinelai-backend",
        "version": "0.10.0",
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
    }


@router.get("/api/ready", summary="Readiness Probe")
@router.get("/ready", summary="Readiness Probe (Direct)")
def readiness_check(
    response: Response,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Readiness Check:
    Verifies critical application dependencies before traffic routing:
    1. Database connectivity (SELECT 1 test query)
    2. Video storage directory accessibility and writability
    """
    checks: Dict[str, Any] = {
        "database": "unknown",
        "storage": "unknown",
    }
    is_ready = True

    # 1. Database Ping Check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "reachable"
    except Exception as e:
        checks["database"] = f"unreachable: {str(e)}"
        is_ready = False

    # 2. Video Storage Writability Check
    try:
        storage_path = settings.VIDEO_STORAGE_PATH
        os.makedirs(storage_path, exist_ok=True)
        test_file = os.path.join(storage_path, ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        if os.path.exists(test_file):
            os.remove(test_file)
        checks["storage"] = "writable"
    except Exception as e:
        checks["storage"] = f"unwritable: {str(e)}"
        is_ready = False

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "sentinelai-backend",
            "ready": False,
            "checks": checks,
        }

    return {
        "status": "ready",
        "service": "sentinelai-backend",
        "ready": True,
        "checks": checks,
    }
