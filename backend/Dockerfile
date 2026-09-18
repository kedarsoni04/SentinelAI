# ==============================================================================
# SentinelAI — Production Backend Dockerfile
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

# Install lightweight CPU-only PyTorch to prevent 2.5GB CUDA download hang
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source and configuration
COPY alembic.ini .
COPY migrations migrations/
COPY app app/
COPY yolo11n.pt* ./

# Ensure storage directories exist with proper permissions
RUN mkdir -p storage/uploads storage/frames storage/annotated

# Expose FastAPI service port
EXPOSE 8000

# Production ASGI server execution: bind to dynamic $PORT from Render, 1 worker to save RAM
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
