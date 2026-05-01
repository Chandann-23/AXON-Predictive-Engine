# AXON Predictive Engine - Distributed Deployment Guide

## Overview
This guide walks you through deploying the AXON Predictive Engine as a distributed system:
- **Backend**: FastAPI on Render (Docker)
- **Frontend**: Streamlit on Vercel (Python Runtime)

---

## Phase 1: Backend Deployment (Render)

### Prerequisites
- Docker Desktop installed
- Render account (free tier available)
- GitHub repository with your code

### Steps

1. **Verify Docker Configuration**
   ```bash
   # Ensure your Dockerfile is in the root
   ls -la Dockerfile
   ```

2. **Deploy to Render**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - **Runtime**: Docker
   - **Root Directory**: `/` (root of repo)
   - **Build Command**: `docker build -t axon-api .`
   - **Start Command**: `docker run -p 8080:8080 axon-api`

3. **Environment Variables**
   - **DATABASE_URL**: PostgreSQL connection string (for production)
     - Format: `postgresql://username:password@host:port/database`
     - Example: `postgresql://user:pass@db.axon.com:5432/axon_db`
   - **Note**: If DATABASE_URL is not set, app will fallback to SQLite

4. **Get Your API URL**
   - Once deployed, copy the "Service URL" from Render dashboard
   - Example: `https://axon-api.onrender.com`

5. **Verify Backend**
   ```bash
   curl https://axon-api.onrender.com/health
   # SQLite: {"status":"ok","db_type":"sqlite","db_connected":true}
   # PostgreSQL: {"status":"ok","db_type":"postgresql","db_connected":true}
   ```

---

## PostgreSQL Setup (Optional but Recommended)

### Option 1: Render PostgreSQL (Easy)
1. **Create Database**
   - Go to Render Dashboard → "New" → "PostgreSQL"
   - Choose a name (e.g., `axon-db`)
   - Select free tier or paid plan

2. **Get Connection String**
   - Once deployed, go to database settings
   - Copy the "Connection" string
   - Format: `postgresql://username:password@host:port/database`

3. **Add to Web Service**
   - In your Render web service settings
   - Add Environment Variable: `DATABASE_URL` = (paste connection string)

### Option 2: External PostgreSQL
- **AWS RDS**, **Google Cloud SQL**, or **DigitalOcean**
- Create database and get connection string
- Add `DATABASE_URL` to Render environment variables

### Option 3: SQLite (Development)
- No setup required
- Automatically used if `DATABASE_URL` is not set
- Perfect for testing and development

---

## Phase 2: Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (free tier available)
- Same GitHub repository

### Steps

1. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**
   - In Vercel dashboard → Settings → Environment Variables
   - Add: `RENDER_API_URL` = `https://axon-api.onrender.com`
   - (Replace with your actual Render URL)

3. **Build Settings**
   - **Framework Preset**: Python
   - **Root Directory**: `/`
   - **Build Command**: (leave blank - detected automatically)
   - **Output Directory**: (leave blank)

4. **Deploy**
   - Click "Deploy"
   - Wait for build completion (~2-3 minutes)

---

## Phase 3: Final Validation

### Check 1: Frontend Access
- Open your Vercel URL
- **Expected**: AXON logo appears with "Predictive Health Engine" subtitle

### Check 2: API Communication
- Move any slider (CPU, RAM, Temp, Latency)
- **Expected**: "AI System Health Gauge" updates with risk percentage
- **Expected**: "LED" indicator changes color based on risk level

### Check 3: Database Persistence
- Refresh the page
- **Expected**: "Global Risk Trajectory" shows historical dots from previous sessions
- **Expected**: "Last AI Pulse" timestamp appears in sidebar

### Check 4: Health Monitoring
- Go to "03 / MLOPS" tab
- **Expected**: API Status shows "ONLINE"
- **Expected**: Inference Latency shows reasonable values (<1000ms)

---

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure `app.py` has `allow_origins=["*"]` in CORSMiddleware
   - Check that Vercel environment variable is set correctly

2. **Database Not Persisting**
   - Verify BASE_DIR logic in `app.py` (lines 14-17)
   - Check that SQLite files are in `src/` folder

3. **Build Failures on Vercel**
   - Ensure `vercel.json` is in root directory
   - Check Python version compatibility (3.9+)

4. **API Timeouts**
   - Render free tier may need 60 seconds to "wake up"
   - Check API health endpoint first

### Debug URLs
- Backend Health: `https://your-render-url.onrender.com/health`
- Backend Docs: `https://your-render-url.onrender.com/docs`
- Frontend: `https://your-vercel-url.vercel.app`

---

## Architecture Diagram

```
Vercel (Frontend)     →    Render (Backend)     →    Database
┌─────────────────┐         ┌─────────────────┐    ┌─────────────┐
│  Streamlit App   │  HTTPS  │   FastAPI       │    │ PostgreSQL  │
│  - UI/Gauges     │ ──────→ │  - /predict     │    │ (Optional)  │
│  - Sliders       │         │  - /history     │    │             │
│  - Charts        │         │  - /health      │    │ SQLite DB   │
│  - Environment   │         │  - ML Model     │    │ (Fallback)  │
│    Variables     │         │  - Auto Table   │    │             │
└─────────────────┘         │    Creation     │    └─────────────┘
     VERCEL_URL                 RENDER_URL
```

---

## Performance Notes

- **Render**: Free tier sleeps after 15min inactivity (60s wake-up)
- **Vercel**: Instant cold starts, no sleep issues
- **Database**: 
  - SQLite: Persists in Docker container
  - PostgreSQL: Production-grade, persistent, scalable
- **Latency**: Expect 200-800ms for API calls

---

## Next Steps

1. **Custom Domain**: Configure custom domains on both platforms
2. **Monitoring**: Add logging/monitoring for production
3. **Scaling**: Upgrade plans for higher traffic
4. **Security**: Add authentication for production use
