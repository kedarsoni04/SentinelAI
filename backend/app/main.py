from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

# Import models so Base.metadata.create_all picks up all tables
from app.models import (  # noqa: F401
    analysis_job,
    analysis_result,
    camera,
    detection,
    incident_report,
    security_event,
    security_rule,
    security_zone,
    track_point,
    tracked_object,
    user,
)


def sync_database_schema():
    """
    Create missing tables and safely extend existing tables if necessary.
    Guards SQLite-specific PRAGMA queries so PostgreSQL connections execute cleanly.
    """
    Base.metadata.create_all(bind=engine)

    # SQLite-specific column migrations for local dev environments
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            try:
                # 1. Update analysis_results columns if missing
                res = conn.execute(text("PRAGMA table_info(analysis_results)")).fetchall()
                col_names = [r[1] for r in res]
                if col_names:
                    if "annotated_frame_path" not in col_names:
                        conn.execute(text("ALTER TABLE analysis_results ADD COLUMN annotated_frame_path VARCHAR(1024)"))
                    if "detection_count" not in col_names:
                        conn.execute(text("ALTER TABLE analysis_results ADD COLUMN detection_count INTEGER NOT NULL DEFAULT 0"))
                    conn.commit()
            except Exception:
                pass

            try:
                # 2. Update detections columns if missing
                res_det = conn.execute(text("PRAGMA table_info(detections)")).fetchall()
                det_cols = [r[1] for r in res_det]
                if det_cols:
                    if "track_id" not in det_cols:
                        conn.execute(text("ALTER TABLE detections ADD COLUMN track_id INTEGER"))
                    if "tracked_object_id" not in det_cols:
                        conn.execute(text("ALTER TABLE detections ADD COLUMN tracked_object_id VARCHAR(36)"))
                    conn.commit()
            except Exception:
                pass

            try:
                # 3. Create incident_reports table columns if missing (backward compat)
                res_ir = conn.execute(text("PRAGMA table_info(incident_reports)")).fetchall()
                ir_cols = [r[1] for r in res_ir]
                if ir_cols:
                    if "prompt_tokens" not in ir_cols:
                        conn.execute(text("ALTER TABLE incident_reports ADD COLUMN prompt_tokens INTEGER"))
                    if "camera_id" not in ir_cols:
                        conn.execute(text("ALTER TABLE incident_reports ADD COLUMN camera_id VARCHAR(36)"))
                    if "incident_status" not in ir_cols:
                        conn.execute(text("ALTER TABLE incident_reports ADD COLUMN incident_status VARCHAR(20) NOT NULL DEFAULT 'OPEN'"))
                    if "resolved_at" not in ir_cols:
                        conn.execute(text("ALTER TABLE incident_reports ADD COLUMN resolved_at DATETIME"))
                    conn.commit()
            except Exception:
                pass


import logging
from app.core.logging import setup_logging
from app.core.middleware import (
    InMemoryRateLimiterMiddleware,
    RequestCorrelationMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.exceptions import setup_exception_handlers

# Configure structured logging
setup_logging(is_production=settings.is_production)
logger = logging.getLogger("sentinel.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Creates database tables on startup if they don't exist.
    """
    logger.info("SentinelAI API service starting up in [%s] mode...", settings.ENVIRONMENT)
    sync_database_schema()
    yield
    logger.info("SentinelAI API service shutting down...")


app = FastAPI(
    title="SentinelAI API",
    description=(
        "AI-Powered Intelligent Surveillance & Threat Detection Platform. "
        "Phase 10: Production Deployment, Observability, Security Hardening & Portfolio Polish."
    ),
    version="0.10.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Exception Handlers ────────────────────────────────────────────────────
setup_exception_handlers(app)

# ─── Middleware Pipeline ───────────────────────────────────────────────────
# Execution order: Outermost added last
app.add_middleware(InMemoryRateLimiterMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestCorrelationMiddleware)

# ─── Routers ────────────────────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/", tags=["System"], summary="API Root")
def root():
    """API root — confirms the service is running."""
    return {
        "service": "SentinelAI API",
        "version": "0.10.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/api/health",
        "ready": "/api/ready",
    }
