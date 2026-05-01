# AXON Distributed Deployment - Validation Checklist

## 🚀 Pre-Deployment Checks

### Backend (Render)
- [ ] Dockerfile exists in root directory
- [ ] `src/app.py` has CORS middleware with `allow_origins=["*"]`
- [ ] BASE_DIR logic implemented (lines 14-17 in app.py)
- [ ] SQLite databases in `src/` folder (`axon_telemetry.db`, `feedback.db`)
- [ ] Model file exists: `models/server_model.pkl`

### Frontend (Vercel)
- [ ] `vercel.json` exists in root directory
- [ ] `src/dashboard.py` imports `os` module
- [ ] All API calls use `os.environ.get("RENDER_API_URL", "fallback_url")`
- [ ] Environment variable placeholder configured

---

## 🌐 Post-Deployment Validation

### Check 1: Frontend Access
**URL**: `https://your-vercel-url.vercel.app`

- [ ] **AXON Logo**: Large gradient "AXON" text appears
- [ ] **Subtitle**: "Predictive Health Engine" visible
- [ ] **Navigation**: Three tabs visible (01 / MONITOR, 02 / DOCUMENTATION, 03 / MLOPS)
- [ ] **No Loading Errors**: Console shows no JavaScript errors

### Check 2: API Communication
**Test**: Move any slider in Monitor tab

- [ ] **Health Gauge Updates**: Risk percentage changes
- [ ] **LED Indicator**: Changes color (green/red) based on risk
- [ ] **Status Text**: Shows "SYSTEM STABLE" or "CRITICAL RISK"
- [ ] **No "Synchronizing" Message**: API responds successfully

### Check 3: Database Persistence
**Test**: Refresh browser page

- [ ] **Historical Data**: "Global Risk Trajectory" shows dots from previous session
- [ ] **Last AI Pulse**: Sidebar shows recent timestamp
- [ ] **Export Button**: Download history works (if data exists)

### Check 4: Health Monitoring
**Navigate to**: 03 / MLOPS tab

- [ ] **API Status**: Shows "ONLINE" (green)
- [ ] **Inference Latency**: Shows reasonable values (<1000ms)
- [ ] **Model Version**: Shows "v1.0.2"
- [ ] **API Inspector**: Shows last JSON response when available

---

## 🔧 Advanced Validation

### Backend API Tests
```bash
# Health Check
curl https://your-render-url.onrender.com/health

# Prediction Test
curl "https://your-render-url.onrender.com/predict?cpu=50&ram=50&temp=45&latency=20"

# History Test
curl https://your-render-url.onrender.com/history
```

Expected Responses:
- [ ] Health: `{"status":"ok","db_connected":true}`
- [ ] Prediction: JSON with `failure_probability`, `status`, `feature_importance`
- [ ] History: Array of objects with timestamp and telemetry data

### Frontend Environment Variable
```bash
# In Vercel dashboard, verify:
RENDER_API_URL = https://your-render-url.onrender.com
```

- [ ] Variable exists in Vercel settings
- [ ] No typos in URL
- [ ] No trailing slash (unless required)

---

## 🐛 Troubleshooting Guide

### Issue: CORS Errors
**Symptoms**: Browser console shows CORS policy errors
**Solutions**:
1. Verify `app.py` line 70: `allow_origins=["*"]`
2. Check Vercel environment variable is correct
3. Ensure backend URL is accessible

### Issue: API Timeouts
**Symptoms**: "AI Engine Synchronizing..." message persists
**Solutions**:
1. Wait 60 seconds for Render to wake up (free tier)
2. Check backend health endpoint directly
3. Verify Render service is running

### Issue: No Historical Data
**Symptoms**: "Waiting for historical telemetry data..." message
**Solutions**:
1. Make at least one prediction first
2. Check SQLite database persistence
3. Verify `/history` endpoint returns data

### Issue: Build Failures
**Symptoms**: Vercel deployment fails
**Solutions**:
1. Check `vercel.json` syntax
2. Verify Python version compatibility
3. Ensure all dependencies in `requirements.txt`

---

## 📊 Performance Benchmarks

### Expected Performance
- **Cold Start (Vercel)**: <3 seconds
- **API Response Time**: 200-800ms
- **Database Query**: <100ms
- **Page Load**: <5 seconds

### Monitoring
- [ ] Check Vercel Analytics for page load times
- [ ] Monitor Render response times
- [ ] Track error rates in both services

---

## ✅ Final Sign-off

### Production Readiness
- [ ] All validation checks pass
- [ ] Performance benchmarks met
- [ ] No console errors
- [ ] Database persistence confirmed
- [ ] Environment variables configured

### Documentation
- [ ] Deployment guide reviewed
- [ ] Troubleshooting guide available
- [ ] Architecture diagram understood
- [ ] Backup procedures documented

---

## 🚨 Rollback Plan

If critical issues arise:

1. **Frontend Issues**: 
   - Check Vercel deployment logs
   - Verify environment variables
   - Rollback to previous commit if needed

2. **Backend Issues**:
   - Check Render service logs
   - Verify Docker configuration
   - Redeploy if necessary

3. **Database Issues**:
   - SQLite should persist in container
   - Check file permissions
   - Verify BASE_DIR logic

---

**Deployment Complete!** 🎉

Your AXON Predictive Engine is now running as a distributed system with:
- **Backend**: FastAPI + SQLite on Render
- **Frontend**: Streamlit on Vercel
- **Database**: Persistent SQLite storage
- **Environment**: Configurable API endpoints
