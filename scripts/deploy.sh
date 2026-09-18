#!/usr/bin/env bash
# ==============================================================================
# SentinelAI — Automated Production Deployment Script
# ==============================================================================
set -euo pipefail

ENV_FILE=".env.prod"

echo "======================================================================"
echo "🛡️  SentinelAI Production Deployment"
echo "======================================================================"

# 1. Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker and Docker Compose."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not available."
    exit 1
fi

# 2. Ensure .env.prod exists
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  $ENV_FILE not found! Generating from .env.production.example..."
    cp .env.production.example "$ENV_FILE"

    # Auto-generate secure random secrets
    POSTGRES_PASS=$(openssl rand -hex 16 2>/dev/null || date +%s | sha256sum | base64 | head -c 32)
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || date +%s%N | sha256sum | head -c 64)

    sed -i "s/POSTGRES_PASSWORD=generate_a_random_32char_password_here/POSTGRES_PASSWORD=$POSTGRES_PASS/" "$ENV_FILE"
    sed -i "s/sentinel:generate_a_random_32char_password_here/sentinel:$POSTGRES_PASS/" "$ENV_FILE"
    sed -i "s/JWT_SECRET_KEY=generate_a_random_64char_hex_secret_here/JWT_SECRET_KEY=$JWT_SECRET/" "$ENV_FILE"

    echo "✅ Generated new secrets in $ENV_FILE"
    echo "👉 Please edit $ENV_FILE to configure your DOMAIN_NAME and GEMINI_API_KEY before continuing."
fi

# 3. Pull / build and launch production stack
echo ""
echo "🚀 Building and starting SentinelAI containers in production mode..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up -d --build

# 4. Wait for database and backend healthchecks
echo ""
echo "⏳ Waiting for services to pass health checks..."
timeout 60 bash -c '
    until [ "$(docker inspect -f {{.State.Health.Status}} sentinelai-postgres 2>/dev/null)" == "healthy" ]; do
        sleep 2
    done
' || echo "⚠️  Postgres healthcheck timed out or unavailable"

timeout 60 bash -c '
    until [ "$(docker inspect -f {{.State.Health.Status}} sentinelai-backend 2>/dev/null)" == "healthy" ]; do
        sleep 2
    done
' || echo "⚠️  Backend healthcheck timed out or unavailable"

# 5. Run database migrations
echo ""
echo "📦 Running Alembic database migrations inside container..."
docker exec sentinelai-backend alembic upgrade head || true

echo ""
echo "======================================================================"
echo "✅ SentinelAI Deployment Complete!"
echo "======================================================================"
echo "Current Container Status:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Useful Commands:"
echo "  • View live logs:    docker compose -f docker-compose.prod.yml logs -f"
echo "  • Backend logs:      docker logs -f sentinelai-backend"
echo "  • Restart stack:     docker compose -f docker-compose.prod.yml restart"
echo "  • Stop stack:        docker compose -f docker-compose.prod.yml down"
echo "======================================================================"
