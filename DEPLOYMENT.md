# 🚀 SentinelAI — Production Deployment Guide

This guide walks you through deploying **SentinelAI** live to a Cloud Virtual Machine (VPS) using Docker Compose, Nginx reverse proxy, and Let's Encrypt SSL.

---

## 🖥️ 1. VM Sizing & Cloud Recommendations

SentinelAI runs Ultralytics YOLOv11 Nano inference, OpenCV frame sampling, ByteTrack multi-object tracking, and a Next.js 14 frontend.

| Tier | Specs | Best For | Estimated Cost |
| :--- | :--- | :--- | :--- |
| **Minimum** | 2 vCPUs, 4 GB RAM, 25 GB SSD | 1–2 video streams, demo/portfolio, low traffic | ~$12 – $24/mo |
| **Recommended** | 4 vCPUs, 8 GB RAM, 50 GB SSD | 3–6 concurrent video analysis jobs, full SOC | ~$28 – $48/mo |
| **GPU Enhanced** | 4+ vCPUs, 16 GB RAM + NVIDIA T4/A10G | Real-time multi-camera 30 FPS inference | ~$0.50 – $1.00/hr |

**Recommended Cloud Providers:**
- **DigitalOcean**: Basic or General Purpose Droplet (Ubuntu 24.04)
- **Hetzner Cloud**: CPX21 / CPX31 (Best price-to-performance in Europe/US)
- **AWS EC2**: `t3.medium` or `t3.large` (CPU) / `g4dn.xlarge` (NVIDIA T4 GPU)
- **Google Cloud**: `e2-standard-2` or `e2-standard-4`

---

## 🌐 2. DNS & Firewall Setup

### DNS Records
At your domain registrar (Cloudflare, Namecheap, GoDaddy, Route53), add an **A Record**:
- **Type**: `A`
- **Host / Name**: `@` (or `sentinel` for a subdomain like `sentinel.example.com`)
- **Value / Target**: `<YOUR_SERVER_PUBLIC_IP>`
- **TTL**: 300 seconds (or Auto)

### Firewall (UFW / Security Groups)
Open only required public ports:
```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```
> [!IMPORTANT]
> Do **NOT** open port `5432` (Postgres) or port `8000` (FastAPI). In our production architecture, these services communicate entirely within a private Docker bridge network. Only Nginx on ports 80 and 443 is exposed to the internet.

---

## 🛠️ 3. Server Preparation (Ubuntu 22.04 / 24.04 LTS)

SSH into your cloud server:
```bash
ssh root@<YOUR_SERVER_PUBLIC_IP>
```

Update packages and install Docker + Docker Compose:
```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git openssl

# 2. Install official Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Verify Docker & Docker Compose
docker --version
docker compose version
```

---

## 📦 4. Clone Repository & Configure Environment

```bash
# 1. Clone your repository
git clone https://github.com/<YOUR_USERNAME>/SentinelAI.git
cd SentinelAI

# 2. Copy the production environment configuration
cp .env.production.example .env.prod

# 3. Edit environment variables
nano .env.prod
```

Configure the following critical values in `.env.prod`:
- `DOMAIN_NAME`: Set to your domain (e.g., `sentinel.yourdomain.com`) or your server IP.
- `ADMIN_EMAIL`: Set to your email for SSL renewal notifications.
- `POSTGRES_PASSWORD`: Replace with a secure 32-character password.
- `JWT_SECRET_KEY`: Generate a 64-char key (`openssl rand -hex 32`).
- `NEXT_PUBLIC_API_URL`: Set to `https://<YOUR_DOMAIN_NAME>` (or `http://<SERVER_IP>` if deploying without a domain).
- `AI_PROVIDER`: Set to `gemini` or `groq` and supply the corresponding API key.

---

## 🚀 5. Deploy Live Stack

Make the deployment scripts executable and run the deploy script:
```bash
chmod +x scripts/deploy.sh scripts/init-ssl.sh
./scripts/deploy.sh
```

The script will:
1. Build optimized Docker images for FastAPI and Next.js.
2. Launch PostgreSQL with internal health checks.
3. Apply database migrations via Alembic.
4. Route requests through the Nginx reverse proxy.

Verify that all 4 containers are running:
```bash
docker compose -f docker-compose.prod.yml ps
```

---

## 🔒 6. Enable Free HTTPS (Let's Encrypt)

Once your DNS `A` record has propagated and points to your server:

```bash
./scripts/init-ssl.sh
```

This will automatically:
1. Request a trusted SSL certificate from Let's Encrypt.
2. Switch Nginx to the hardened HTTPS configuration.
3. Start the background Certbot container which automatically renews certificates every 60 days.

---

## 🩺 7. Health & Sanity Checks

Verify your deployment from your terminal or browser:

| Endpoint | Test Command | Expected Result |
| :--- | :--- | :--- |
| **Frontend** | `curl -I https://<YOUR_DOMAIN>` | `HTTP/2 200` |
| **API Health** | `curl https://<YOUR_DOMAIN>/api/health` | `{"status": "healthy", ...}` |
| **API Ready** | `curl https://<YOUR_DOMAIN>/api/ready` | `{"database": "connected", ...}` |
| **WebSockets** | Visit `/live-monitoring` in UI | `CONNECTED` badge active |

---

## 🔄 8. Ongoing Maintenance & Operations

### View Real-Time Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f --tail=100

# Specific service (backend / frontend / nginx / postgres)
docker logs -f sentinelai-backend
```

### Database Backup
```bash
docker exec -t sentinelai-postgres pg_dump -U sentinel sentinelai > backup_$(date +%Y%m%d).sql
```

### Pull Updates & Redeploy
```bash
git pull origin main
./scripts/deploy.sh
```
