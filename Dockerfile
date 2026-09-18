# ==============================================================================
# SentinelAI — Root Dockerfile for Cloud Platforms (Render, Railway, Fly.io)
# Base: Python 3.11 Slim Debian
# ==============================================================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

WORKDIR /app

# Install essential system dependencies for OpenCV and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libpq-dev \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from backend directory
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source and configuration
COPY backend/alembic.ini .
COPY backend/migrations migrations/
COPY backend/app app/
COPY backend/yolo11n.pt* yolo11n.pt* ./

# Ensure storage directories exist
RUN mkdir -p storage/uploads storage/frames storage/annotated

# Expose FastAPI service port
EXPOSE 8000

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production ASGI server execution
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
