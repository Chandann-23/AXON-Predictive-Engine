# Predictive Maintenance MLOps Project

This project implements an end-to-end MLOps workflow for predictive maintenance of server health. It generates synthetic telemetry logs, trains a classification model to predict failure risk, tracks experiments with MLflow, and serves predictions through a production-ready FastAPI API.

## Architecture Overview

The project follows a simple but professional MLOps architecture:

- **Data Layer (`data/`)**
  - `generate_logs.py` creates synthetic server telemetry.
  - `system_logs.csv` stores the generated training dataset.
- **Training Layer (`src/train.py`)**
  - Loads data and trains a `RandomForestClassifier`.
  - Logs hyperparameters and metrics to MLflow.
  - Saves trained artifact to `models/server_model.pkl`.
- **Serving Layer (`src/app.py`)**
  - FastAPI service exposes:
    - `GET /health` for service status.
    - `POST /predict` for failure risk scoring.
- **Model Layer (`models/`)**
  - Stores the model artifact used by the API.
- **CI Layer (`.github/workflows/main.yml`)**
  - Runs on every push.
  - Installs dependencies, regenerates data, retrains model, and validates model artifact existence.
- **Container Layer (`Dockerfile`)**
  - Packages the app with a lightweight Python runtime and starts the API with `uvicorn`.

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── main.yml
├── data/
│   ├── generate_logs.py
│   └── system_logs.csv
├── models/
│   └── server_model.pkl
├── src/
│   ├── app.py
│   └── train.py
├── Dockerfile
├── README.md
└── requirements.txt
```

## Local Setup

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate data:

```bash
python data/generate_logs.py
```

## Training With MLflow

Run training:

```bash
python src/train.py
```

What gets logged to MLflow:

- Parameter: `n_estimators`
- Metrics: `accuracy`, `f1_score`

Artifacts:

- Model file: `models/server_model.pkl`

## Run the API Locally

Start the FastAPI server:

```bash
uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Test endpoints:

- Health check: `GET http://127.0.0.1:8000/health`
- Prediction: `POST http://127.0.0.1:8000/predict`

Example prediction payload:

```json
{
  "cpu": 92,
  "ram": 88,
  "temp": 83,
  "latency": 210
}
```

## Docker Usage

Build image:

```bash
docker build -t server-health-mlops .
```

Run container:

```bash
docker run --rm -p 8000:8000 -p 8501:8501 server-health-mlops
```

Then visit:

- API: `http://127.0.0.1:8000/health`
- API Documentation: `http://127.0.0.1:8000/docs`
- **Frontend Dashboard**: `http://127.0.0.1:8501`

## Frontend Dashboard

The Streamlit dashboard allows real-time server health monitoring. Adjust sliders for CPU, RAM, Temperature, and Latency to see the model's prediction and the System Health Gauge.

## CI Pipeline

The GitHub Actions workflow in `.github/workflows/main.yml` automatically:

1. Triggers on every push.
2. Installs Python and project dependencies.
3. Generates the dataset.
4. Trains the model.
5. Verifies `models/server_model.pkl` exists.
