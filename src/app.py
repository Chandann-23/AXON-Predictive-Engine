from pathlib import Path
import pickle
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pydantic import BaseModel, Field

# 1. Define the Data Models
class PredictionResponse(BaseModel):
    failure_probability: float
    status: str
    feature_importance: dict[str, float]

# 2. Model Loader
def load_model() -> Any:
    # Looks for 'models/server_model.pkl' relative to this file
    project_root = Path(__file__).resolve().parents[1]
    model_path = project_root / "models" / "server_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    with model_path.open("rb") as model_file:
        return pickle.load(model_file)

# 3. Initialize App
app = FastAPI(title="AXON Predictive Engine API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the AI model once when the server starts
model = load_model()

@app.get("/")
def read_root():
    return {"message": "AXON Engine is Live! Use /predict?cpu=50&ram=50&temp=45&latency=20"}

# 4. FIXED PREDICT ROUTE (Now uses GET to match your Dashboard)
@app.get("/predict", response_model=PredictionResponse)
def predict(
    cpu: float = Query(..., ge=0, le=100),
    ram: float = Query(..., ge=0, le=100),
    temp: float = Query(..., ge=0),
    latency: float = Query(..., ge=0)
):
    try:
        # Create DataFrame for the model
        features_df = pd.DataFrame([
            {
                "cpu_usage": cpu,
                "ram_usage": ram,
                "temp_celsius": temp,
                "network_latency": latency,
            }
        ])

        # Run AI Inference
        # We use [0][1] because predict_proba returns [Probability of 0, Probability of 1]
        probs = model.predict_proba(features_df)
        failure_probability = float(probs[0][1])
        
        # Extract feature importance from the model
        feature_names = ["CPU", "RAM", "Temp", "Latency"]
        importances = model.feature_importances_
        feature_importance = dict(zip(feature_names, [float(i) for i in importances]))
        
        # Determine Status
        status = "CRITICAL RISK" if failure_probability >= 0.8 else ("WARNING" if failure_probability >= 0.5 else "STABLE")

        return PredictionResponse(
            failure_probability=round(failure_probability, 4),
            status=status,
            feature_importance=feature_importance
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI Prediction failed: {exc}")

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Random Forest"}