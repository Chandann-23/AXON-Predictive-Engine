import os
import sqlite3
import pickle
from pathlib import Path
from sqlalchemy import create_engine
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest

def retrain_model():
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "data" / "feedback.db"
    model_path = project_root / "models" / "server_model.pkl"
    anomaly_model_path = project_root / "models" / "anomaly_model.pkl"
    data_path = project_root / "data" / "system_logs.csv"

    # 1. Load Original Data
    if not data_path.exists():
        print("Original data not found. Retraining skipped.")
        return
    df_original = pd.read_csv(data_path)
    
    # 2. Load Feedback Data (Supabase or SQLite fallback)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        print("Retriever: Fetching feedback from PostgreSQL/Supabase DB...")
        try:
            engine = create_engine(database_url)
            df_feedback = pd.read_sql_query("SELECT cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, label FROM feedback", engine)
            print(f"Retriever: Successfully fetched {len(df_feedback)} samples from Supabase.")
        except Exception as e:
            print(f"Error fetching from Supabase PostgreSQL: {e}")
            return
    else:
        print(f"Retriever: Fetching feedback from local SQLite: {db_path}")
        if not db_path.exists():
            print("Feedback database file not found. Retraining skipped.")
            return
            
        try:
            conn = sqlite3.connect(db_path)
            df_feedback = pd.read_sql_query("SELECT cpu, ram, temp, latency, disk_io, swap_usage, net_throughput, thread_count, label FROM feedback", conn)
            conn.close()
            print(f"Retriever: Successfully fetched {len(df_feedback)} samples from SQLite.")
        except Exception as e:
            print(f"Error reading local SQLite feedback: {e}")
            return

    if df_feedback.empty:
        print("No feedback data found. Retraining skipped.")
        return

    # 3. Process Feedback
    df_feedback['failure'] = 0
    df_feedback = df_feedback.rename(columns={
        'cpu': 'cpu_usage',
        'ram': 'ram_usage',
        'temp': 'temp_celsius',
        'latency': 'network_latency',
        'disk_io': 'disk_io',
        'swap_usage': 'swap_usage',
        'net_throughput': 'net_throughput',
        'thread_count': 'thread_count'
    })
    df_feedback = df_feedback[['cpu_usage', 'ram_usage', 'temp_celsius', 'network_latency', 'disk_io', 'swap_usage', 'net_throughput', 'thread_count', 'failure']]

    # 4. Combine Datasets
    df_combined = pd.concat([df_original, df_feedback, df_feedback, df_feedback], ignore_index=True)

    # 5. Retrain both models
    features = [
        "cpu_usage", "ram_usage", "temp_celsius", "network_latency",
        "disk_io", "swap_usage", "net_throughput", "thread_count"
    ]
    X = df_combined[features]
    y = df_combined["failure"]

    # Retrain Supervised Model
    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X, y)

    # Retrain Unsupervised Model
    anomaly_model = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
    anomaly_model.fit(X)

    # 6. Save Models
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)
        
    with anomaly_model_path.open("wb") as anomaly_file:
        pickle.dump(anomaly_model, anomaly_file)

    print(f"Model successfully retrained with {len(df_feedback)} feedback samples.")
    print(f"Supervised model saved to: {model_path}")
    print(f"Unsupervised model saved to: {anomaly_model_path}")
    return True

if __name__ == "__main__":
    retrain_model()
