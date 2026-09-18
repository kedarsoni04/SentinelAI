#!/usr/bin/env bash
# ==============================================================================
# SentinelAI — Automated SSL Setup with Let's Encrypt / Certbot
# ==============================================================================
set -euo pipefail

if [ ! -f .env.prod ]; then
    echo "❌ Error: .env.prod file not found. Run scripts/deploy.sh first."
    exit 1
fi

source .env.prod

if [ -z "${DOMAIN_NAME:-}" ] || [ "$DOMAIN_NAME" = "yourdomain.com" ]; then
    echo "❌ Error: DOMAIN_NAME is not set properly in .env.prod"
    exit 1
fi

if [ -z "${ADMIN_EMAIL:-}" ] || [ "$ADMIN_EMAIL" = "admin@yourdomain.com" ]; then
    echo "❌ Error: ADMIN_EMAIL is not set properly in .env.prod"
    exit 1
fi

echo "🔐 Setting up Let's Encrypt SSL certificate for: $DOMAIN_NAME..."

# 1. Request the certificate using certbot container
docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $ADMIN_EMAIL \
    -d $DOMAIN_NAME \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal" certbot

# 2. Substitute DOMAIN_NAME into the SSL nginx template
sed "s/\${DOMAIN_NAME}/$DOMAIN_NAME/g" nginx/nginx.ssl.conf.template > nginx/nginx.conf

# 3. Reload nginx to activate SSL
docker exec sentinelai-nginx nginx -s reload

echo "✅ SSL certificate issued and HTTPS is live at https://$DOMAIN_NAME"
