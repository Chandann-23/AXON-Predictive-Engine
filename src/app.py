from pathlib import Path
import pickle
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    cpu: float = Field(..., ge=0, le=100)
    ram: float = Field(..., ge=0, le=100)
    temp: float = Field(..., ge=0)
    latency: float = Field(..., ge=0)


class PredictionResponse(BaseModel):
    failure_probability: float
    status: str
    feature_importance: dict[str, float]


def load_model() -> Any:
    project_root = Path(__file__).resolve().parents[1]
    model_path = project_root / "models" / "server_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    with model_path.open("rb") as model_file:
        return pickle.load(model_file)


app = FastAPI(title="Server Health Predictive Maintenance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)
model = load_model()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "predictive-maintenance-api"}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    try:
        features_df = pd.DataFrame(
            [
                {
                    "cpu_usage": request.cpu,
                    "ram_usage": request.ram,
                    "temp_celsius": request.temp,
                    "network_latency": request.latency,
                }
            ]
        )
        failure_probability = float(model.predict_proba(features_df)[0][1])
        
        # Extract feature importance
        feature_names = ["CPU", "RAM", "Temp", "Latency"]
        importances = model.feature_importances_
        feature_importance = dict(zip(feature_names, [float(i) for i in importances]))
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    status = "Warning: High Risk" if failure_probability >= 0.5 else "Normal"
    return PredictionResponse(
        failure_probability=round(failure_probability, 4),
        status=status,
        feature_importance=feature_importance
    )
@app.get("/")
def read_root():
    return {"message": "Server is running! Use /predict for AI analysis."}

@app.get("/predict")
def predict(cpu: float, ram: float, temp: float, latency: float):
    # your model prediction logic here...
    return {"prediction": 0.85, "factors": ["High CPU"]}