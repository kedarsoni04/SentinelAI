from fastapi import APIRouter

from app.api.routes import (
    analytics,
    auth,
    cameras,
    health,
    incidents,
    realtime,
    security_events,
    video_analysis,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cameras.router)
api_router.include_router(video_analysis.router)
api_router.include_router(security_events.router)
api_router.include_router(realtime.router)
api_router.include_router(incidents.router)
api_router.include_router(analytics.router)
