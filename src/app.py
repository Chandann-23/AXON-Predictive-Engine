from pathlib import Path
import pickle
from typing import Any, List
import sqlite3
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pydantic import BaseModel, Field

# 1. Define the Data Models
class PredictionResponse(BaseModel):
    failure_probability: float
    status: str
    feature_importance: dict[str, float]

class FeedbackRequest(BaseModel):
    cpu: float
    ram: float
    temp: float
    latency: float
    label: str

# 2. Database Initialization
def init_db():
    project_root = Path(__file__).resolve().parents[1]
    
    # Feedback DB
    db_path = project_root / "feedback.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu REAL,
            ram REAL,
            temp REAL,
            latency REAL,
            label TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

    # Telemetry DB
    telemetry_db_path = project_root / "axon_telemetry.db"
    conn_tel = sqlite3.connect(telemetry_db_path)
    cursor_tel = conn_tel.cursor()
    cursor_tel.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cpu REAL,
            ram REAL,
            temp REAL,
            latency REAL,
            failure_probability REAL,
            status TEXT
        )
    ''')
    conn_tel.commit()
    conn_tel.close()

init_db()

# 3. Model Loader
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

        # Log to Telemetry DB
        try:
            project_root = Path(__file__).resolve().parents[1]
            telemetry_db_path = project_root / "axon_telemetry.db"
            conn = sqlite3.connect(telemetry_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO history (cpu, ram, temp, latency, failure_probability, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cpu, ram, temp, latency, round(failure_probability, 4), status))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"Telemetry logging failed: {db_err}")

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

@app.get("/history")
def get_history():
    try:
        project_root = Path(__file__).resolve().parents[1]
        telemetry_db_path = project_root / "axon_telemetry.db"
        conn = sqlite3.connect(telemetry_db_path)
        # Configure row_factory to return dictionaries
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM history 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert sqlite3.Row objects to dictionaries
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {e}")

@app.post("/feedback")
def receive_feedback(feedback: FeedbackRequest):
    try:
        project_root = Path(__file__).resolve().parents[1]
        db_path = project_root / "feedback.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (cpu, ram, temp, latency, label, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (feedback.cpu, feedback.ram, feedback.temp, feedback.latency, feedback.label, datetime.now()))
        conn.commit()
        conn.close()
        return {"message": "Feedback recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {e}")