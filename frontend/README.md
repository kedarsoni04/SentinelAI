# 🛡️ SentinelAI — Frontend SOC Dashboard

A modern, high-performance Security Operations Center (SOC) dashboard built with **Next.js 14** (App Router), **TypeScript**, and **Tailwind CSS**.

---

## 🌐 Live Deployments

| Component | Production URL | Description |
| :--- | :--- | :--- |
| **Frontend Web Console** | 🔗 **[https://sentinel-ai-olive.vercel.app/](https://sentinel-ai-olive.vercel.app/)** | Live Next.js 14 SOC Dashboard on Vercel |
| **Backend API Service** | 🔗 **[https://sentinelai-backend-s3cz.onrender.com](https://sentinelai-backend-s3cz.onrender.com)** | Live FastAPI Backend & WebSocket Stream on Render |
| **Interactive API Docs** | 🔗 **[https://sentinelai-backend-s3cz.onrender.com/docs](https://sentinelai-backend-s3cz.onrender.com/docs)** | OpenAPI Swagger Documentation |

> [!TIP]
> **Cold Starts**: Render free/starter instances may take 30–50 seconds to spin up on cold start after a period of inactivity.

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- Node.js 18.17+ or 20+
- Running SentinelAI Backend (locally on `http://localhost:8000` or using the production backend)

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment Variables
Create or edit `.env.local`:
```env
# Point to local FastAPI backend or live cloud backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For live backend connection during local development:
```env
NEXT_PUBLIC_API_URL=https://sentinelai-backend-s3cz.onrender.com
```

### 4. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to access the SentinelAI SOC Operations Console.

---

## 📦 Build for Production

```bash
# Build production bundle
npm run build

# Run production server
npm start
```

---

## 📁 Key Application Routes

- `/login` — Operator authentication & JWT management
- `/register` — Account creation
- `/dashboard` — SOC Overview & quick metrics
- `/dashboard/cameras` — Camera stream management (RTSP, Webcam, HTTP)
- `/dashboard/analysis` — Video processing, YOLOv11 detections & ByteTrack trajectory viewer
- `/dashboard/zones` — Spatial polygonal restricted zones setup
- `/dashboard/rules` — Threat detection rule engine (Intrusion, Loitering, Crowd Density)
- `/dashboard/monitoring` — Real-time WebSocket surveillance telemetry & audible alert stream
- `/dashboard/incidents` — AI-synthesized incident reports & operator triage
- `/dashboard/analytics` — Historical security heatmaps, risk scores & statistical anomaly spikes
