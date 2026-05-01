from pathlib import Path
import pickle

import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


def train_model(n_estimators: int = 200, random_state: int = 42) -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "system_logs.csv"
    model_path = project_root / "models" / "server_model.pkl"

    df = pd.read_csv(data_path)
    features = ["cpu_usage", "ram_usage", "temp_celsius", "network_latency"]
    target = "failure"

    X = df[features]
    y = df[target]

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

    mlflow.set_experiment("server-health-predictive-maintenance")
    with mlflow.start_run():
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)

    print(f"Model saved to: {model_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-Score: {f1:.4f}")


if __name__ == "__main__":
    train_model()
