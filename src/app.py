import sqlite3
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, List
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- 1. PATH CONFIGURATION (The "Render-Safe" Way) ---
# This ensures SQLite creates the DB in the same folder as this script
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR.parent / "models"
TELEMETRY_DB = BASE_DIR / "axon_telemetry.db"
FEEDBACK_DB = BASE_DIR / "feedback.db"

# --- 2. DATABASE CONFIGURATION ---
# Support both PostgreSQL (production) and SQLite (development)
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"Using PostgreSQL: {DATABASE_URL}")
else:
    # SQLite configuration (fallback)
    print("Using SQLite fallback")
    engine = None
    SessionLocal = None

# --- 2. DATA MODELS ---
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

# --- 3. DATABASE INITIALIZATION ---
def init_dbs():
    if USE_POSTGRES:
        # Initialize PostgreSQL tables
        with engine.connect() as conn:
            # Create telemetry table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu REAL, ram REAL, temp REAL, latency REAL,
                    failure_probability REAL, status TEXT
                )
            """))
            
            # Create feedback table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    cpu REAL, ram REAL, temp REAL, latency REAL,
                    label TEXT, timestamp TIMESTAMP
                )
            """))
            conn.commit()
            print("PostgreSQL tables initialized")
    else:
        # Initialize SQLite databases
        with sqlite3.connect(TELEMETRY_DB) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu REAL, ram REAL, temp REAL, latency REAL,
                    failure_probability REAL, status TEXT
                )
            ''')
        
        with sqlite3.connect(FEEDBACK_DB) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu REAL, ram REAL, temp REAL, latency REAL,
                    label TEXT, timestamp DATETIME
                )
            ''')
        print("SQLite databases initialized")

init_dbs()

# --- 4. MODEL LOADER ---
def load_model() -> Any:
    model_path = MODELS_DIR / "server_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    with open(model_path, "rb") as f:
        return pickle.load(f)

# --- 5. APP INITIALIZATION ---
app = FastAPI(title="AXON Predictive Engine", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = load_model()

# --- 6. ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "AXON Engine is Live! Use /predict?cpu=50&ram=50&temp=45&latency=20"}

@app.head("/")
def head_root():
    return None

@app.get("/health")
def health():
    if USE_POSTGRES:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ok", "db_type": "postgresql", "db_connected": True}
        except Exception as e:
            return {"status": "error", "db_type": "postgresql", "db_connected": False, "error": str(e)}
    else:
        return {"status": "ok", "db_type": "sqlite", "db_connected": TELEMETRY_DB.exists()}

@app.get("/predict", response_model=PredictionResponse)
def predict(
    cpu: float = Query(..., ge=0, le=100),
    ram: float = Query(..., ge=0, le=100),
    temp: float = Query(..., ge=0),
    latency: float = Query(..., ge=0)
):
    try:
        # AI Inference
        features = pd.DataFrame([{
            "cpu_usage": cpu, "ram_usage": ram, 
            "temp_celsius": temp, "network_latency": latency
        }])
        prob = float(model.predict_proba(features)[0][1])
        
        # Feature Importance
        feat_names = ["CPU", "RAM", "Temp", "Latency"]
        feat_imp = dict(zip(feat_names, [float(i) for i in model.feature_importances_]))
        
        status = "CRITICAL" if prob >= 0.8 else ("WARNING" if prob >= 0.5 else "STABLE")

        # PERSISTENCE: Log to Database
        if USE_POSTGRES:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO history (cpu, ram, temp, latency, failure_probability, status)
                    VALUES (:cpu, :ram, :temp, :latency, :prob, :status)
                """), {
                    "cpu": cpu, "ram": ram, "temp": temp, "latency": latency,
                    "prob": round(prob, 4), "status": status
                })
                conn.commit()
        else:
            with sqlite3.connect(TELEMETRY_DB) as conn:
                conn.execute('''
                    INSERT INTO history (cpu, ram, temp, latency, failure_probability, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (cpu, ram, temp, latency, round(prob, 4), status))

        return PredictionResponse(
            failure_probability=round(prob, 4),
            status=status,
            feature_importance=feat_imp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    try:
        if USE_POSTGRES:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM history 
                    ORDER BY timestamp DESC 
                    LIMIT 50
                """))
                rows = result.fetchall()
                # Convert to dict format
                return [dict(row._mapping) for row in rows]
        else:
            with sqlite3.connect(TELEMETRY_DB) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 50")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        return {"error": "History unavailable", "details": str(e)}

@app.post("/feedback")
def receive_feedback(feedback: FeedbackRequest):
    try:
        if USE_POSTGRES:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO feedback (cpu, ram, temp, latency, label, timestamp)
                    VALUES (:cpu, :ram, :temp, :latency, :label, :timestamp)
                """), {
                    "cpu": feedback.cpu, "ram": feedback.ram, "temp": feedback.temp,
                    "latency": feedback.latency, "label": feedback.label,
                    "timestamp": datetime.now()
                })
                conn.commit()
        else:
            with sqlite3.connect(FEEDBACK_DB) as conn:
                conn.execute('''
                    INSERT INTO feedback (cpu, ram, temp, latency, label, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (feedback.cpu, feedback.ram, feedback.temp, feedback.latency, feedback.label, datetime.now()))
        return {"message": "Feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))