---
title: AXON Predictive Engine API
emoji: 📡
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# AXON Predictive Engine — Backend API

FastAPI backend powering the AXON Predictive Engine dashboard.

**Endpoints:**
- `GET /health` — API health check
- `GET /predict` — Run AI failure prediction
- `GET /history` — Fetch telemetry history logs
- `POST /feedback` — Submit operator feedback
- `GET /mlops/stats` — Drift detection & MLOps stats
- `POST /mlops/retrain` — Trigger async model retraining
