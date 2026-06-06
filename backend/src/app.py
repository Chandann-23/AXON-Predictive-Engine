import sqlite3
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, List
import os
import threading
from scipy.stats import ks_2samp
from src.retrain import retrain_model

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- 1. PATH CONFIGURATION (Unified Data & Model Directories) ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
MODELS_DIR = BASE_DIR.parent / "models"

TELEMETRY_DB = DATA_DIR / "axon_telemetry.db"
FEEDBACK_DB = DATA_DIR / "feedback.db"

# Ensure folders exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- 2. DATABASE CONFIGURATION ---
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    # PostgreSQL configuration (Supabase)
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"Using PostgreSQL: {DATABASE_URL}")
else:
    # SQLite configuration (Local fallback)
    print("Using SQLite fallback")
    engine = None
    SessionLocal = None

# --- 2. DATA MODELS ---
class PredictionResponse(BaseModel):
    failure_probability: float
    status: str
    feature_importance: dict[str, float]
    local_explainability: dict[str, float]
    anomaly_detected: bool
    anomaly_score: float

class FeedbackRequest(BaseModel):
    cpu: float
    ram: float
    temp: float
    latency: float
    disk_io: float
    swap_usage: float
    net_throughput: float
    thread_count: float
    label: str

# --- 3. DATABASE INITIALIZATION ---
def init_dbs():
    if USE_POSTGRES:
        # Initialize PostgreSQL tables (for Supabase)
        try:
            with engine.connect() as conn:
                # Create telemetry table with anomaly and new metrics support
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS history (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        cpu REAL, ram REAL, temp REAL, latency REAL,
                        disk_io REAL DEFAULT 0.0,
                        swap_usage REAL DEFAULT 0.0,
                        net_throughput REAL DEFAULT 0.0,
                        thread_count REAL DEFAULT 0.0,
                        failure_probability REAL, status TEXT,
                        anomaly_detected BOOLEAN DEFAULT FALSE,
                        anomaly_score REAL DEFAULT 0.0
                    )
                """))
                
                # Check and add anomaly & new telemetry columns if table existed but lacked them
                try:
                    conn.execute(text("ALTER TABLE history ADD COLUMN IF NOT EXISTS anomaly_detected BOOLEAN DEFAULT FALSE"))
                    conn.execute(text("ALTER TABLE history ADD COLUMN IF NOT EXISTS anomaly_score REAL DEFAULT 0.0"))
                except Exception as ex:
                    print(f"Col checks bypassed: {ex}")

                for col in ["disk_io", "swap_usage", "net_throughput", "thread_count"]:
                    try:
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN IF NOT EXISTS {col} REAL DEFAULT 0.0"))
                    except Exception as ex:
                        print(f"Column check bypass for {col}: {ex}")

                # Create feedback table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        cpu REAL, ram REAL, temp REAL, latency REAL,
                        disk_io REAL DEFAULT 0.0,
                        swap_usage REAL DEFAULT 0.0,
                        net_throughput REAL DEFAULT 0.0,
                        thread_count REAL DEFAULT 0.0,
                        label TEXT, timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                for col in ["disk_io", "swap_usage", "net_throughput", "thread_count"]:
                    try:
                        conn.execute(text(f"ALTER TABLE feedback ADD COLUMN IF NOT EXISTS {col} REAL DEFAULT 0.0"))
                    except Exception as ex:
                        print(f"Feedback column check bypass for {col}: {ex}")

                conn.commit()
                print("PostgreSQL tables successfully initialized")
        except Exception as e:
            print(f"PostgreSQL Table initialization error: {e}")
    else:
        # Initialize local SQLite databases
        with sqlite3.connect(TELEMETRY_DB) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu REAL, ram REAL, temp REAL, latency REAL,
                    disk_io REAL DEFAULT 0.0,
                    swap_usage REAL DEFAULT 0.0,
                    net_throughput REAL DEFAULT 0.0,
                    thread_count REAL DEFAULT 0.0,
                    failure_probability REAL, status TEXT,
                    anomaly_detected BOOLEAN DEFAULT 0,
                    anomaly_score REAL DEFAULT 0.0
                )
            ''')
            # Safe migrations
            for col in ["disk_io", "swap_usage", "net_throughput", "thread_count"]:
                try:
                    conn.execute(f"ALTER TABLE history ADD COLUMN {col} REAL DEFAULT 0.0")
                except:
                    pass
        
        with sqlite3.connect(FEEDBACK_DB) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu REAL, ram REAL, temp REAL, latency REAL,
                    disk_io REAL DEFAULT 0.0,
                    swap_usage REAL DEFAULT 0.0,
                    net_throughput REAL DEFAULT 0.0,
                    thread_count REAL DEFAULT 0.0,
                    label TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Safe migrations
            for col in ["disk_io", "swap_usage", "net_throughput", "thread_count"]:
                try:
                    conn.execute(f"ALTER TABLE feedback ADD COLUMN {col} REAL DEFAULT 0.0")
                except:
                    pass
        print("SQLite databases successfully initialized")

init_dbs()

# --- 4. MODEL LOADERS ---
def load_model() -> Any:
    model_path = MODELS_DIR / "server_model.pkl"
    if not model_path.exists():
        print(f"Warning: Supervised model not found at {model_path}. Run train.py first.")
        return None
    with open(model_path, "rb") as f:
        return pickle.load(f)

def load_anomaly_model() -> Any:
    anomaly_path = MODELS_DIR / "anomaly_model.pkl"
    if not anomaly_path.exists():
        print(f"Warning: Unsupervised anomaly model not found at {anomaly_path}. Run train.py first.")
        return None
    with open(anomaly_path, "rb") as f:
        return pickle.load(f)

# --- 5. APP INITIALIZATION ---
app = FastAPI(title="AXON Predictive Engine Backend", version="2.1.0")

# CORS setup (Stateless API: disabled credentials to safely allow wildcard origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = load_model()
anomaly_model = load_anomaly_model()

# --- 5. MLOPS & DRIFT DETECTION GLOBALS ---
retraining_in_progress = False
baseline_df = None
baseline_means = {}
baseline_stds = {}

try:
    baseline_path = DATA_DIR / "system_logs.csv"
    if baseline_path.exists():
        baseline_df = pd.read_csv(baseline_path)
        print(f"Loaded drift baseline data with {len(baseline_df)} rows")
    else:
        print(f"Warning: Baseline data not found at {baseline_path} for drift analysis.")
except Exception as e:
    print(f"Error loading baseline dataset: {e}")

# Calculate baseline averages and standard deviations for SHAP local explainability
default_means = {
    "cpu": 62.0, "ram": 68.0, "temp": 62.0, "latency": 120.0,
    "disk_io": 35.0, "swap_usage": 15.0, "net_throughput": 250.0, "thread_count": 350.0
}
default_stds = {
    "cpu": 20.0, "ram": 18.0, "temp": 16.0, "latency": 55.0,
    "disk_io": 20.0, "swap_usage": 12.0, "net_throughput": 180.0, "thread_count": 150.0
}

if baseline_df is not None:
    for col_name, key in [("cpu_usage", "cpu"), ("ram_usage", "ram"), ("temp_celsius", "temp"), ("network_latency", "latency"),
                          ("disk_io", "disk_io"), ("swap_usage", "swap_usage"), ("net_throughput", "net_throughput"), ("thread_count", "thread_count")]:
        if col_name in baseline_df.columns:
            baseline_means[key] = float(baseline_df[col_name].mean())
            baseline_stds[key] = float(baseline_df[col_name].std())

for k in default_means:
    if k not in baseline_means:
        baseline_means[k] = default_means[k]
    if k not in baseline_stds or baseline_stds[k] <= 0:
        baseline_stds[k] = default_stds[k]

def reload_active_models():
    global model, anomaly_model
    try:
        new_model = load_model()
        new_anomaly = load_anomaly_model()
        if new_model is not None:
            model = new_model
        if new_anomaly is not None:
            anomaly_model = new_anomaly
        print("Successfully reloaded active ML models in memory (hot-swapped)")
    except Exception as e:
        print(f"Failed to hot-swap reloaded models: {e}")

def calculate_drift():
    global baseline_df
    if baseline_df is None:
        try:
            baseline_path = DATA_DIR / "system_logs.csv"
            if baseline_path.exists():
                baseline_df = pd.read_csv(baseline_path)
        except:
            pass
            
    if baseline_df is None:
        return False, {}, "Baseline dataset missing"

    # Fetch live telemetry from the database (last 30 items)
    live_data = []
    try:
        if USE_POSTGRES:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count 
                    FROM history 
                    ORDER BY timestamp DESC 
                    LIMIT 30
                """))
                live_data = [dict(row._mapping) for row in result.fetchall()]
        else:
            with sqlite3.connect(TELEMETRY_DB) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count 
                    FROM history 
                    ORDER BY timestamp DESC 
                    LIMIT 30
                """)
                live_data = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        return False, {}, f"Database read failure: {e}"

    # Check if we have enough samples for a K-S test
    if len(live_data) < 10:
        return False, {}, "Insufficient telemetry history (need >= 10 pulses to perform drift analysis)"

    # Align features
    # Baseline columns: cpu_usage, ram_usage, temp_celsius, network_latency, disk_io, swap_usage, net_throughput, thread_count
    # DB columns: cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count
    features_mapping = {
        "CPU": ("cpu_usage", "cpu"),
        "RAM": ("ram_usage", "ram"),
        "Temp": ("temp_celsius", "temp"),
        "Latency": ("network_latency", "latency"),
        "Disk I/O": ("disk_io", "disk_io"),
        "Swap": ("swap_usage", "swap_usage"),
        "Net": ("net_throughput", "net_throughput"),
        "Threads": ("thread_count", "thread_count")
    }

    drift_metrics = {}
    drift_detected = False

    for feature_name, (baseline_col, live_col) in features_mapping.items():
        baseline_vals = baseline_df[baseline_col].dropna().values
        live_vals = [r[live_col] for r in live_data if r[live_col] is not None]
        
        if len(live_vals) < 10:
            drift_metrics[feature_name] = {
                "p_value": 1.0,
                "ks_statistic": 0.0,
                "drifted": False,
                "status": "INSUFFICIENT_DATA"
            }
            continue

        # Perform Kolmogorov-Smirnov test
        stat, p_val = ks_2samp(baseline_vals, live_vals)
        
        is_drifted = bool(p_val < 0.05)
        if is_drifted:
            drift_detected = True

        drift_metrics[feature_name] = {
            "p_value": round(float(p_val), 5),
            "ks_statistic": round(float(stat), 5),
            "drifted": is_drifted,
            "status": "DRIFTED" if is_drifted else "STABLE"
        }

    return drift_detected, drift_metrics, "Drift analysis complete"

def get_feedback_count() -> int:
    try:
        if USE_POSTGRES:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM feedback"))
                return result.scalar() or 0
        else:
            with sqlite3.connect(FEEDBACK_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM feedback")
                return cursor.fetchone()[0]
    except Exception as e:
        print(f"Error reading feedback count: {e}")
        return 0

def run_async_retrain():
    global retraining_in_progress
    try:
        retraining_in_progress = True
        print("Background retraining worker started.")
        success = retrain_model()
        if success:
            reload_active_models()
            print("Background retraining worker completed successfully.")
        else:
            print("Background retraining worker skipped/failed.")
    except Exception as e:
        print(f"Error during background retraining task: {e}")
    finally:
        retraining_in_progress = False

# --- 6. ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "AXON Hybrid Backend is Live! Outlier detection (Isolation Forest) is active."}

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
    latency: float = Query(..., ge=0),
    disk_io: float = Query(0.0, ge=0, le=100),
    swap_usage: float = Query(0.0, ge=0, le=100),
    net_throughput: float = Query(0.0, ge=0, le=1000),
    thread_count: float = Query(0.0, ge=0, le=1000)
):
    global model, anomaly_model
    if model is None:
        model = load_model()
    if anomaly_model is None:
        anomaly_model = load_anomaly_model()
        
    if model is None or anomaly_model is None:
        raise HTTPException(
            status_code=500, 
            detail="Machine learning model artifacts are missing. Please run train.py to initialize models."
        )

    try:
        # Format metrics into DataFrame for inference
        features = pd.DataFrame([{
            "cpu_usage": cpu, "ram_usage": ram, 
            "temp_celsius": temp, "network_latency": latency,
            "disk_io": disk_io, "swap_usage": swap_usage,
            "net_throughput": net_throughput, "thread_count": thread_count
        }])
        
        # 1. Supervised Prediction (Random Forest)
        prob = float(model.predict_proba(features)[0][1])
        status = "CRITICAL" if prob >= 0.8 else ("WARNING" if prob >= 0.5 else "STABLE")
        
        # Feature Importance weights
        feat_names = ["CPU", "RAM", "Temp", "Latency", "Disk I/O", "Swap", "Net", "Threads"]
        feat_imp = dict(zip(feat_names, [float(i) for i in model.feature_importances_]))
        
        # Compute local SHAP-style contributions
        raw_contributions = {
            "CPU": ((cpu - baseline_means["cpu"]) / max(0.1, baseline_stds["cpu"])) * model.feature_importances_[0],
            "RAM": ((ram - baseline_means["ram"]) / max(0.1, baseline_stds["ram"])) * model.feature_importances_[1],
            "Temp": ((temp - baseline_means["temp"]) / max(0.1, baseline_stds["temp"])) * model.feature_importances_[2],
            "Latency": ((latency - baseline_means["latency"]) / max(0.1, baseline_stds["latency"])) * model.feature_importances_[3],
            "Disk I/O": ((disk_io - baseline_means["disk_io"]) / max(0.1, baseline_stds["disk_io"])) * model.feature_importances_[4],
            "Swap": ((swap_usage - baseline_means["swap_usage"]) / max(0.1, baseline_stds["swap_usage"])) * model.feature_importances_[5],
            "Net": ((net_throughput - baseline_means["net_throughput"]) / max(0.1, baseline_stds["net_throughput"])) * model.feature_importances_[6],
            "Threads": ((thread_count - baseline_means["thread_count"]) / max(0.1, baseline_stds["thread_count"])) * model.feature_importances_[7]
        }
        
        sum_abs = sum(abs(v) for v in raw_contributions.values())
        local_explainability = {}
        if sum_abs > 0:
            delta_p = float(prob - 0.10)
            for feat, val in raw_contributions.items():
                local_explainability[feat] = round(delta_p * (val / sum_abs), 4)
        else:
            local_explainability = {feat: 0.0 for feat in raw_contributions}

        # 2. Unsupervised Anomaly Scoring (Isolation Forest)
        # Predict outputs 1 (normal) or -1 (anomaly)
        anomaly_pred = int(anomaly_model.predict(features)[0])
        anomaly_detected = anomaly_pred == -1
        # decision_function gives a continuous anomaly score (lower means more anomalous)
        anomaly_score = float(anomaly_model.decision_function(features)[0])

        # PERSISTENCE: Log run transaction to database
        if USE_POSTGRES:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO history (cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, failure_probability, status, anomaly_detected, anomaly_score)
                    VALUES (:cpu, :ram, :temp, :latency, :disk_io, :swap_usage, :net_throughput, :thread_count, :prob, :status, :anomaly_detected, :anomaly_score)
                """), {
                    "cpu": cpu, "ram": ram, "temp": temp, "latency": latency,
                    "disk_io": disk_io, "swap_usage": swap_usage, "net_throughput": net_throughput, "thread_count": thread_count,
                    "prob": round(prob, 4), "status": status,
                    "anomaly_detected": anomaly_detected, "anomaly_score": round(anomaly_score, 4)
                })
                conn.commit()
        else:
            with sqlite3.connect(TELEMETRY_DB) as conn:
                conn.execute('''
                    INSERT INTO history (cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, failure_probability, status, anomaly_detected, anomaly_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, round(prob, 4), status, anomaly_detected, round(anomaly_score, 4)))

        return PredictionResponse(
            failure_probability=round(prob, 4),
            status=status,
            feature_importance=feat_imp,
            local_explainability=local_explainability,
            anomaly_detected=anomaly_detected,
            anomaly_score=round(anomaly_score, 4)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    try:
        if USE_POSTGRES:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, timestamp, cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, failure_probability, status, anomaly_detected, anomaly_score 
                    FROM history 
                    ORDER BY timestamp DESC 
                    LIMIT 15
                """))
                rows = result.fetchall()
                output = []
                for row in rows:
                    r_dict = dict(row._mapping)
                    if r_dict.get('timestamp') is not None:
                        r_dict['timestamp'] = r_dict['timestamp'].isoformat()
                    output.append(r_dict)
                return output
        else:
            with sqlite3.connect(TELEMETRY_DB) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, failure_probability, status, anomaly_detected, anomaly_score 
                    FROM history 
                    ORDER BY timestamp DESC 
                    LIMIT 15
                """)
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
                    INSERT INTO feedback (cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, label, timestamp)
                    VALUES (:cpu, :ram, :temp, :latency, :disk_io, :swap_usage, :net_throughput, :thread_count, :label, :timestamp)
                """), {
                    "cpu": feedback.cpu, "ram": feedback.ram, "temp": feedback.temp, "latency": feedback.latency,
                    "disk_io": feedback.disk_io, "swap_usage": feedback.swap_usage,
                    "net_throughput": feedback.net_throughput, "thread_count": feedback.thread_count,
                    "label": feedback.label, "timestamp": datetime.now()
                })
                conn.commit()
        else:
            with sqlite3.connect(FEEDBACK_DB) as conn:
                conn.execute('''
                    INSERT INTO feedback (cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, label, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (feedback.cpu, feedback.ram, feedback.temp, feedback.latency, feedback.disk_io, feedback.swap_usage, feedback.net_throughput, feedback.thread_count, feedback.label, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Post-feedback hook: check count to trigger automatic retraining
        cnt = get_feedback_count()
        if cnt > 0 and cnt % 5 == 0:
            print(f"Feedback threshold reached ({cnt}). Triggering automatic async retrain.")
            if not retraining_in_progress:
                thread = threading.Thread(target=run_async_retrain)
                thread.daemon = True
                thread.start()
                
        return {"message": "Feedback recorded successfully", "feedback_count": cnt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mlops/stats")
def get_mlops_stats():
    drift_detected, drift_metrics, drift_msg = calculate_drift()
    feedback_count = get_feedback_count()
    
    # Determine live sample size from database history
    live_size = 0
    try:
        if USE_POSTGRES:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM history"))
                live_size = result.scalar() or 0
        else:
            with sqlite3.connect(TELEMETRY_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM history")
                live_size = cursor.fetchone()[0]
    except:
        pass
        
    return {
        "drift_detected": drift_detected,
        "drift_metrics": drift_metrics,
        "drift_message": drift_msg,
        "retraining_in_progress": retraining_in_progress,
        "feedback_count": feedback_count,
        "baseline_sample_size": len(baseline_df) if baseline_df is not None else 0,
        "live_sample_size": min(30, live_size),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/mlops/retrain")
def force_retrain():
    global retraining_in_progress
    if retraining_in_progress:
        raise HTTPException(status_code=400, detail="Retraining is already in progress.")
        
    thread = threading.Thread(target=run_async_retrain)
    thread.daemon = True
    thread.start()
    return {"message": "Asynchronous retraining job triggered successfully.", "status": "triggered"}
