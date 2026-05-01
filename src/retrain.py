import sqlite3
import pandas as pd
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

def retrain_model():
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "feedback.db"
    model_path = project_root / "models" / "server_model.pkl"
    data_path = project_root / "data" / "system_logs.csv"

    # 1. Load Original Data
    if not data_path.exists():
        print("Original data not found. Retraining skipped.")
        return
    df_original = pd.read_csv(data_path)
    
    # 2. Load Feedback Data
    if not db_path.exists():
        print("Feedback database not found. Retraining skipped.")
        return
        
    conn = sqlite3.connect(db_path)
    df_feedback = pd.read_sql_query("SELECT cpu, ram, temp, latency, label FROM feedback", conn)
    conn.close()

    if df_feedback.empty:
        print("No feedback data found. Retraining skipped.")
        return

    # 3. Process Feedback
    # Map 'false_positive' to the correct target label. 
    # If it was reported as a false positive, the true label should be 0 (Stable).
    df_feedback['failure'] = 0
    df_feedback = df_feedback.rename(columns={
        'cpu': 'cpu_usage',
        'ram': 'ram_usage',
        'temp': 'temp_celsius',
        'latency': 'network_latency'
    })
    df_feedback = df_feedback[['cpu_usage', 'ram_usage', 'temp_celsius', 'network_latency', 'failure']]

    # 4. Combine Datasets
    # We weight feedback data more heavily or just append it. 
    # For a simple retrain, we append it multiple times to ensure the model learns from the corrections.
    df_combined = pd.concat([df_original, df_feedback, df_feedback, df_feedback], ignore_index=True)

    # 5. Retrain
    features = ["cpu_usage", "ram_usage", "temp_celsius", "network_latency"]
    X = df_combined[features]
    y = df_combined["failure"]

    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X, y)

    # 6. Save Model
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)

    print(f"Model successfully retrained with {len(df_feedback)} feedback samples.")
    print(f"New model saved to: {model_path}")

if __name__ == "__main__":
    retrain_model()
