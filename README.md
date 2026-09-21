<div align="center">

# 🛡️ SentinelAI

### **AI-Powered Intelligent Surveillance & Threat Detection Platform**

[![Live Frontend Demo](https://img.shields.io/badge/Live_Demo-Frontend-00C7B7.svg?style=for-the-badge&logo=vercel&logoColor=white)](https://sentinel-ai-olive.vercel.app/)
[![Live Backend API](https://img.shields.io/badge/Live_API-Backend-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://sentinelai-backend-s3cz.onrender.com/docs)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js_14-App_Router-black.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](./LICENSE)

<p align="center">
  <b>A production-grade, full-stack Security Operations Center (SOC) platform combining edge-ready computer vision, YOLOv11 object detection, ByteTrack multi-object tracking, real-time WebSocket telemetry, rule-based threat classification, GenAI-assisted incident intelligence, and historical security analytics.</b>
</p>

[🌐 Live Deployments](#-live-deployments--demo-links) •
[System Architecture](#-system-architecture) •
[Data Flow](#-complete-surveillance-data-flow) •
[Features](#-key-capabilities-phases-110) •
[Docker Quickstart](#-docker-quickstart) •
[Local Development](#-local-development-setup) •
[API Reference](#-api-reference) •
[Security & Observability](#-security-hardening--observability)

---

</div>

## 🌐 Live Deployments & Demo Links

SentinelAI is deployed live in production:

| Service / Resource | Target Link | Status & Details |
| :--- | :--- | :--- |
| **Frontend Web Console** | 🔗 **[https://sentinel-ai-olive.vercel.app/](https://sentinel-ai-olive.vercel.app/)** | Real-time Dark SOC dashboard (Next.js 14, TypeScript, Tailwind CSS on Vercel) |
| **Backend API Service** | 🔗 **[https://sentinelai-backend-s3cz.onrender.com](https://sentinelai-backend-s3cz.onrender.com)** | Core FastAPI backend, computer vision pipeline, and WebSocket gateway on Render |
| **Interactive API Docs (Swagger UI)** | 🔗 **[https://sentinelai-backend-s3cz.onrender.com/docs](https://sentinelai-backend-s3cz.onrender.com/docs)** | Test live endpoints, inspect schemas, and authorize JWT sessions |
| **API Schema (ReDoc)** | 🔗 **[https://sentinelai-backend-s3cz.onrender.com/redoc](https://sentinelai-backend-s3cz.onrender.com/redoc)** | Clean specification view of all endpoints and models |
| **Health Liveness Probe** | 🔗 **[https://sentinelai-backend-s3cz.onrender.com/api/health](https://sentinelai-backend-s3cz.onrender.com/api/health)** | Live service uptime, version info, and operational health |
| **Live WebSocket Endpoint** | `wss://sentinelai-backend-s3cz.onrender.com/api/ws/analysis/{job_id}` | Authenticated real-time streaming channel for alerts & telemetry |

> [!TIP]
> **Cold Start Note**: Render free/starter instances automatically hibernate after periods of inactivity. If accessing the live backend after idle time, please allow 30–50 seconds for the cloud backend to complete its initial cold start.

### 🔑 Demo Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@sentinelai.io` | `Admin123!` |
| **Security Operator** | `operator@sentinelai.io` | `Operator123!` |

*(You can also register a custom account directly at [https://sentinel-ai-olive.vercel.app/register](https://sentinel-ai-olive.vercel.app/register))*

---

## 📌 Executive Summary

**SentinelAI** transforms passive surveillance video into proactive, actionable security intelligence. Traditional CCTV systems suffer from alert fatigue, operator blindness, and delayed forensic investigation. SentinelAI addresses these challenges through a unified, 10-phase engineering architecture:

1. **Non-Blocking Ingestion**: Streams, decodes, and intelligently samples video frames using headless OpenCV.
2. **Deep Vision AI**: Runs state-of-the-art Ultralytics **YOLOv11** object detection to identify persons, vehicles, and assets.
3. **Temporal Intelligence**: Employs **ByteTrack** with Kalman filtering to maintain persistent track IDs and motion trajectories across frames.
4. **Automated Threat Rules**: Evaluates spatial security zones and temporal behaviors (Intrusion, Loitering, Crowd Density, Unusual Motion) frame-by-frame.
5. **Real-Time SOC Streaming**: Dispatches instant telemetry and security events over authenticated WebSockets to a cyber-grade Dark SOC dashboard.
6. **AI Incident Intelligence**: Synthesizes complex multi-event timelines into human-readable incident reports and risk triage using Gemini, Groq, or fallback mock LLMs.
7. **Longitudinal Analytics**: Aggregates threat distributions, camera risk scoring, hourly activity heatmaps, and statistical anomaly spikes.
8. **Production Engineering**: Hardened with PostgreSQL connection pooling, Alembic migrations, rate limiting, request tracing, and multi-stage Docker containerization.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (SOC Operator)"]
        UI["Next.js 14 Dark SOC Dashboard\n(App Router / TypeScript / Tailwind CSS)"]
        WSClient["WebSocket Client\n(Real-Time Alerts & Telemetry)"]
        AxiosClient["Axios Client Interceptors\n(JWT Auth / Auto-Refresh)"]
    end

    subgraph Gateway ["Edge & Routing Layer"]
        ReverseProxy["Reverse Proxy / Docker Network\n(CORS / Security Headers / Rate Limiter)"]
        ReqCorrelator["Request ID Correlation\n(X-Request-ID Context Tracing)"]
    end

    subgraph AppService ["FastAPI Backend Application"]
        AuthRouter["/api/auth (JWT & Bcrypt)"]
        CameraRouter["/api/cameras (RTSP / Streams)"]
        VisionRouter["/api/video-analysis (Pipeline)"]
        EventRouter["/api/security-events (Rules & Zones)"]
        RealtimeRouter["/api/ws/analysis (WebSockets)"]
        IncidentRouter["/api/incidents (AI Reports)"]
        AnalyticsRouter["/api/analytics (Spike Detection)"]
        HealthRouter["/api/health & /api/ready (Probes)"]
    end

    subgraph VisionEngine ["Computer Vision & Intelligence Subsystem"]
        CVReader["OpenCV Headless Decoder\n(VideoReader & FrameSampler)"]
        YOLOv11["Ultralytics YOLOv11 Nano\n(ModelManager Singleton)"]
        ByteTracker["ByteTrack Multi-Object Tracker\n(Kalman Filter / Trajectories)"]
        RuleEngine["Spatial Rule Evaluation Engine\n(Intrusion / Loitering / Density)"]
        LLMAdapter["AI Provider Factory\n(Gemini 2.0 / Groq / Fallback Mock)"]
    end

    subgraph DataStorage ["Persistence & Storage Layer"]
        PostgresDB[("PostgreSQL 16 Database\n(SQLAlchemy 2.0 / Alembic)")]
        FileStorage[("Persistent Storage Volume\n(/storage/uploads, /frames, /annotated)")]
    end

    UI --> AxiosClient & WSClient
    AxiosClient --> ReverseProxy
    WSClient --> ReverseProxy
    ReverseProxy --> ReqCorrelator --> AppService

    VisionRouter --> CVReader --> YOLOv11 --> ByteTracker --> RuleEngine
    RuleEngine --> EventRouter
    EventRouter --> RealtimeRouter
    IncidentRouter --> LLMAdapter

    AppService --> PostgresDB
    VisionEngine --> FileStorage
```

---

## 🔄 Complete Surveillance Data Flow

```text
Surveillance Stream / File (RTSP, Webcam, MP4, AVI, MKV)
                         │
                         ▼
             POST /api/video-analysis/upload
                         │
                         ▼
        FastAPI Background Task Pipeline Runner
                         │
                         ▼
           OpenCV Video Decoding & Metadata
        (FPS, Total Frames, Resolution, Aspect Ratio)
                         │
                         ▼
             Intelligent Frame Sampling
         (Configurable 2.0s Interval Sampling)
                         │
                         ▼
           YOLOv11 Deep Object Detection
      (Class Confidence Filtering: Person, Vehicle)
                         │
                         ▼
          ByteTrack Multi-Object Association
   (Kalman Filtering, Persistent Track IDs, Trajectory)
                         │
                         ▼
           Spatial Security Zone Rule Engine
 (Polygon Ray-Casting: Intrusion, Loitering, Crowd Density)
                         │
                         ▼
          Security Event Generation & Alerts
                         │
        ┌────────────────┼────────────────┐
        ▼                                 ▼
Database Persistence            WebSocket Dispatch
 (SecurityEvent, TrackedObject)   (Instant SOC Operator Notification)
        │                                 │
        ▼                                 ▼
AI Incident Report Synthesis      Live SOC Monitoring Console
 (Context Prompt -> LLM Summary)   (Bounding Boxes + Trajectory Trails)
        │                                 │
        ▼                                 ▼
Incident Resolution Workflow      Longitudinal Analytics & Anomaly Spikes
```

---

## 🚀 Key Capabilities (Phases 1–10)

| Phase | Module | Status | Highlights & Capabilities |
|:---:|---|:---:|---|
| **01** | **Authentication & RBAC** | ✅ Complete | JWT token lifecycle, bcrypt hashing, `ADMIN` / `SECURITY_OPERATOR` / `VIEWER` roles, protected routes. |
| **02** | **Camera Management** | ✅ Complete | RTSP, Webcam, HTTP Stream, and File source configuration; credentials masking; stream health tracking. |
| **03** | **Video Processing** | ✅ Complete | Headless OpenCV video decoding, intelligent frame sampling, background task workers, thumbnail extraction. |
| **04** | **YOLOv11 Detection** | ✅ Complete | Singleton `ModelManager`, confidence thresholds, dark SOC palette bounding box rendering, category summaries. |
| **05** | **ByteTrack Tracking** | ✅ Complete | Persistent track IDs across frames, trajectory distance & net displacement calculations, job-isolated sessions. |
| **06** | **Security Rule Engine** | ✅ Complete | Polygonal security zones, rule triggers (Intrusion, Loitering, Crowd Density, Unusual Movement), evidence snapshots. |
| **07** | **Real-Time SOC Streaming** | ✅ Complete | In-memory event publisher, authenticated WebSocket streams, live FPS telemetry, real-time alert triage. |
| **08** | **AI Incident Intelligence** | ✅ Complete | Structured LLM prompt engineering, Gemini 2.0 & Groq support, graceful mock fallback, human review actions. |
| **09** | **Analytics & Anomaly Engine** | ✅ Complete | Statistical baseline deviation (Z-score spikes), camera risk scoring, hourly activity heatmaps, incident resolution. |
| **10** | **Production & Observability** | ✅ Complete | Multi-stage Docker, PostgreSQL connection pooling, Alembic migrations, rate limiting, request tracing, CI/CD. |

---

## 🛠️ Technology Stack

```text
Frontend
├── Next.js 14 (App Router & Standalone Output)
├── TypeScript 5.0+
├── Tailwind CSS (Custom Dark SOC Cyberpunk Theme)
├── Lucide React Icons
└── Axios (Centralized Interceptors & Token Management)

Backend
├── Python 3.11+ / FastAPI 0.115+
├── SQLAlchemy 2.0 (Dual Engine: SQLite Dev / PostgreSQL Prod)
├── Alembic 1.14+ (Schema Migrations)
├── Pydantic v2 & Pydantic-Settings (Validated Schemas)
├── Python-Jose & Passlib (JWT & Bcrypt Security)
└── Starlette WebSockets & Streaming Responses

Computer Vision & AI
├── Ultralytics YOLOv11 (Nano Model Singleton)
├── ByteTrack Multi-Object Tracker (Kalman State Filter)
├── OpenCV Headless 4.10+ (Video Pipeline & Annotations)
├── Google Generative AI (Gemini 2.0 Flash)
└── Groq SDK (Llama 3.3 / Qwen Fast Inference)

DevOps & Infrastructure
├── Docker & Multi-Stage Builds
├── Docker Compose (PostgreSQL 16 + Backend + Frontend)
├── GitHub Actions CI (Typechecks, Pytest, Next.js Build)
└── Structured JSON Logging (Request ID Correlation)
```

---

## 🐳 Docker Quickstart

The fastest way to deploy the entire SentinelAI stack (PostgreSQL + FastAPI + Next.js) is via Docker Compose:

### 1. Clone the Repository
```bash
git clone https://github.com/kedarsoni04/SentinelAI.git
cd SentinelAI
```

### 2. Configure Environment (Optional)
The default `docker-compose.yml` runs out-of-the-box with pre-configured development defaults:
- **Frontend**: `http://localhost:3000` (Production Live: [sentinel-ai-olive.vercel.app](https://sentinel-ai-olive.vercel.app/))
- **Backend API**: `http://localhost:8000` (Production Live: [sentinelai-backend-s3cz.onrender.com](https://sentinelai-backend-s3cz.onrender.com))
- **API Documentation**: `http://localhost:8000/docs` (Production Live: [sentinelai-backend-s3cz.onrender.com/docs](https://sentinelai-backend-s3cz.onrender.com/docs))
- **PostgreSQL**: `localhost:5432`

### 3. Build & Launch Containers
```bash
docker compose up --build
```

### 4. Verify System Health
```bash
# Liveness probe
curl http://localhost:8000/api/health

# Readiness probe (verifies database + storage)
curl http://localhost:8000/api/ready
```

---

## 💻 Local Development Setup

SentinelAI is engineered for seamless local development with zero external dependencies using SQLite.

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (or rely on auto-sync in dev)
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run Next.js development server
npm run dev
```

Visit `http://localhost:3000` to access the SentinelAI SOC Operations Console.

---

## 🗄️ Database Management & Migrations

SentinelAI supports a dual-database architecture:
- **Development**: Zero-config SQLite database (`sqlite:///./sentinel.db`)
- **Production**: High-concurrency PostgreSQL (`postgresql://...`)

### Alembic Migration Commands
```bash
cd backend

# Apply all pending migrations to the database
alembic upgrade head

# Create an auto-generated migration based on model changes
alembic revision --autogenerate -m "describe_schema_change"

# View current database revision
alembic current

# Rollback one migration step
alembic downgrade -1
```

---

## 🔒 Security Hardening & Observability

### Security Architecture
- **Cryptographic JWTs**: Validated signatures, strict expiration (`HS256`), and production secret length enforcement (minimum 32 characters).
- **Password Protection**: Passwords hashed with `bcrypt` (12 rounds) via `passlib`; hashes are excluded from all API responses.
- **Ownership Isolation**: Every resource (Cameras, Analysis Jobs, Security Rules, Incident Reports) enforces database-level tenant isolation (`WHERE user_id = current_user.id`).
- **HTTP Security Headers**: Enforced on all responses:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Rate Limiting**: In-memory token bucket protects sensitive endpoints against brute-force attacks:
  - `/api/auth/login` & `/api/auth/register`: 15 requests/minute
  - `/api/incidents`: 20 requests/minute
- **Stream Credential Masking**: All RTSP/HTTP camera URLs automatically mask user credentials in logs and operational displays (`rtsp://admin:***@192.168.1.50`).

### Observability & Probes
- **Request Tracing**: `RequestCorrelationMiddleware` extracts or generates `X-Request-ID` across every HTTP transaction, propagating trace IDs into structured JSON log entries.
- **Liveness vs. Readiness**:
  - **Liveness** (`GET /api/health`): Confirms the process is running, returning service version and uptime.
  - **Readiness** (`GET /api/ready`): Actively executes a `SELECT 1` database query and verifies persistent storage writability before traffic routing.

---

## 📋 API Reference

- **Production API Base**: `https://sentinelai-backend-s3cz.onrender.com`
- **Interactive Swagger UI**: [https://sentinelai-backend-s3cz.onrender.com/docs](https://sentinelai-backend-s3cz.onrender.com/docs)
- **ReDoc Schema Explorer**: [https://sentinelai-backend-s3cz.onrender.com/redoc](https://sentinelai-backend-s3cz.onrender.com/redoc)
- **Local API Base**: `http://localhost:8000`

| Group | Method | Endpoint | Description | Auth Required |
|---|---|---|---|:---:|
| **Health** | `GET` | `/api/health` | Liveness probe & uptime | No |
| | `GET` | `/api/ready` | Readiness probe (DB + Storage check) | No |
| **Auth** | `POST` | `/api/auth/register` | Create operator account | No |
| | `POST` | `/api/auth/login` | Authenticate & retrieve Bearer JWT | No |
| | `GET` | `/api/auth/me` | Fetch authenticated user profile | Yes |
| **Cameras** | `GET` | `/api/cameras` | List configured surveillance cameras | Yes |
| | `POST` | `/api/cameras` | Register new camera stream source | Yes |
| | `PUT` | `/api/cameras/{id}` | Update camera parameters | Yes |
| | `DELETE` | `/api/cameras/{id}` | Decommission camera | Yes |
| **Analysis** | `POST` | `/api/video-analysis/upload` | Upload surveillance video file | Yes |
| | `GET` | `/api/video-analysis` | List video processing jobs | Yes |
| | `GET` | `/api/video-analysis/{id}` | Job metadata, progress & metrics | Yes |
| | `GET` | `/api/video-analysis/{id}/results` | Sampled & annotated frames | Yes |
| | `GET` | `/api/video-analysis/{id}/summary` | YOLO detection summary metrics | Yes |
| | `GET` | `/api/video-analysis/{id}/tracking` | ByteTrack trajectory summary | Yes |
| **Rules & Zones**| `GET` | `/api/security-zones` | List spatial security zones | Yes |
| | `POST` | `/api/security-zones` | Define polygonal restricted zone | Yes |
| | `GET` | `/api/security-rules` | List security detection rules | Yes |
| | `POST` | `/api/security-rules` | Create threat detection rule | Yes |
| **Events** | `GET` | `/api/security-events` | List detected security events | Yes |
| | `PATCH` | `/api/security-events/{id}/status` | Triage event status (ACK/RESOLVE) | Yes |
| **WebSockets** | `WS` | `/api/ws/analysis/{job_id}` | Authenticated real-time event stream | Yes |
| **Incidents** | `POST` | `/api/incidents` | Generate AI Incident Report | Yes |
| | `GET` | `/api/incidents` | List AI incident reports | Yes |
| | `GET` | `/api/incidents/{id}` | Fetch structured AI analysis & timeline | Yes |
| | `PATCH` | `/api/incidents/{id}/status` | Update incident resolution state | Yes |
| **Analytics** | `GET` | `/api/analytics/overview` | High-level SOC metrics & KPI counts | Yes |
| | `GET` | `/api/analytics/trends` | Time-series event frequency | Yes |
| | `GET` | `/api/analytics/cameras` | Per-camera risk scoring & activity | Yes |
| | `GET` | `/api/analytics/heatmap` | 24x7 Day/Hour security heatmap | Yes |
| | `GET` | `/api/analytics/anomalies` | Statistical baseline spike detection | Yes |

---

## 🧪 Testing & Verification

The test suite validates authentication, computer vision singleton behavior, YOLO inference, ByteTrack Kalman filtering, WebSocket session isolation, longitudinal analytics, and production security:

```bash
cd backend

# Run the complete test suite (47 tests)
python -m pytest tests -v
```

All 47 tests execute against SQLite in-memory/test fixtures, running in under 10 seconds.

---

## 🎬 Operator Demonstration Flow

To demonstrate the full end-to-end capabilities of SentinelAI to recruiters or engineering interviewers:

> [!NOTE]
> You can test either on the **Live Production Deployment** at **[https://sentinel-ai-olive.vercel.app/](https://sentinel-ai-olive.vercel.app/)** or locally on `http://localhost:3000`.

1. **Access SOC Portal**: Navigate to `https://sentinel-ai-olive.vercel.app/login` (or `http://localhost:3000/login`) and log in with operator credentials.
2. **Camera Inventory**: Open **Cameras** (`/dashboard/cameras`) to inspect registered RTSP and webcam sources.
3. **Upload Surveillance Footage**: In **Video Analysis** (`/dashboard/analysis`), upload a security test video (`.mp4`).
4. **Inspect YOLO Detection**: View real-time progress. Upon completion, open the job to review category breakdowns (Persons vs. Vehicles) and bounding boxes in the Frame Inspector.
5. **Explore Object Tracking**: Switch to the **Tracked Objects Explorer** to inspect persistent Track IDs, trajectory trails, and net spatial displacement.
6. **Define Restricted Zones**: In **Security Zones** (`/dashboard/zones`), draw a polygon defining a restricted area.
7. **Configure Threat Rules**: In **Security Rules** (`/dashboard/rules`), enable an **Intrusion** or **Loitering** rule for that zone.
8. **Live Real-Time Monitoring**: Open **Live Monitoring** (`/dashboard/monitoring`) to watch WebSocket event streams trigger desktop audio/visual alerts as objects enter the zone.
9. **Synthesize AI Incident Report**: Navigate to **Incidents** (`/dashboard/incidents`) and click **Generate AI Report**. Observe the automated executive summary, chronological timeline, and mitigation steps.
10. **Analyze Trends & Anomalies**: Open **Security Analytics** (`/dashboard/analytics`) to explore event distribution charts, camera risk rankings, activity heatmaps, and statistical anomaly spike detections.

---

## 🌟 Portfolio Technical Highlights

- **Full-Stack Mastery**: Built with Next.js 14 App Router, TypeScript, and FastAPI, maintaining strict type safety from database models to frontend UI components.
- **Edge Computer Vision**: Implemented headless OpenCV frame decoding and frame sampling to eliminate redundant CPU/GPU cycles.
- **State-of-the-Art Detection & Tracking**: Integrated Ultralytics YOLOv11 for bounding box detection coupled with ByteTrack for Kalman-filtered multi-object identity persistence.
- **Resilient Real-Time Concurrency**: Utilized asynchronous WebSockets with in-memory Pub/Sub event distribution and reconnection recovery.
- **AI Agentic Workflows**: Context-sanitizing prompt builder that generates actionable SOC intelligence without leaking PII or raw video frames.
- **DevOps & Production Readiness**: Dual database support (SQLite/PostgreSQL), Alembic migrations, rate limiting, request tracing headers, and multi-stage containerization.

---

## 📄 License

SentinelAI is licensed under the [MIT License](./LICENSE).
