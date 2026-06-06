from pathlib import Path
import pickle

import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


def train_model(n_estimators: int = 200, random_state: int = 42) -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "system_logs.csv"
    model_path = project_root / "models" / "server_model.pkl"
    anomaly_model_path = project_root / "models" / "anomaly_model.pkl"

    df = pd.read_csv(data_path)
    features = [
        "cpu_usage", "ram_usage", "temp_celsius", "network_latency",
        "disk_io", "swap_usage", "net_throughput", "thread_count"
    ]
    target = "failure"

    X = df[features]
    y = df[target]

    # --- 1. Supervised Learning: Random Forest ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=n_estimators, random_state=random_state, n_jobs=-1
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions)

    # --- 2. Unsupervised Learning: Isolation Forest (Anomaly Detection) ---
    # Contamination set to 5% (assumes roughly 5% of data is anomalous outliers)
    anomaly_model = IsolationForest(
        contamination=0.05,
        random_state=random_state,
        n_jobs=-1
    )
    # Unsupervised: fits on features only, without target labels
    anomaly_model.fit(X)

    # Log metrics to MLflow
    mlflow.set_experiment("server-health-predictive-maintenance")
    with mlflow.start_run():
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_param("unsupervised_model", "IsolationForest")
        mlflow.log_param("contamination", 0.05)

    # Save both model files
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)
        
    with anomaly_model_path.open("wb") as anomaly_file:
        pickle.dump(anomaly_model, anomaly_file)

    print(f"Supervised model saved to: {model_path}")
    print(f"Unsupervised anomaly model saved to: {anomaly_model_path}")
    print(f"Random Forest Accuracy: {accuracy:.4f}")
    print(f"Random Forest F1-Score: {f1:.4f}")


if __name__ == "__main__":
    train_model()
