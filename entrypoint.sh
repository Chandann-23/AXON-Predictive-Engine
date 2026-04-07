#!/bin/bash

# Start the FastAPI server in the background
echo "Starting FastAPI server..."
uvicorn src.app:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit dashboard in the foreground
echo "Starting Streamlit dashboard..."
streamlit run src/dashboard.py --server.port 8501 --server.address 0.0.0.0
