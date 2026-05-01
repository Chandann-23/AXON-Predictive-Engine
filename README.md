# AXON Predictive Engine 🚀 #

Industrial IoT Telemetry & AI-Driven Predictive Analytics

AXON is a distributed, full-stack AI application designed for real-time thermal monitoring and predictive maintenance. Unlike monolithic scripts, AXON is built as a decoupled system featuring a Dockerized backend, a serverless PostgreSQL database, and a cloud-native dashboard.

## 🛠️ System Architecture
The project demonstrates a professional-grade Multi-Cloud Distributed Architecture:

Frontend: Streamlit hosted on Streamlit Community Cloud for high-performance data visualization.

Backend (The Brain): FastAPI/Uvicorn service containerized with Docker and deployed on Render.

Database (Memory): Serverless PostgreSQL hosted on Neon, utilizing SQLAlchemy for robust ORM and data persistence.

Communication: RESTful API handshakes with Cross-Origin Resource Sharing (CORS) security protocols.

## ✨ Key Features
AI-Driven Health Scoring: Implements Scikit-learn models (Decision Trees/Random Forests) to predict system health based on telemetry input.

Persistent Telemetry: A custom-built pipeline that saves every "pulse" of data to a remote SQL database, ensuring no data loss during server restarts.

Real-time Visualization: Interactive Plotly charts for monitoring CPU, RAM, and Thermal fluctuations.

Industrial IoT Simulation: Software-based telemetry generation designed for easy integration with physical hardware sensors.

## 🏗️ Tech Stack
Languages: Python 3.10+

AI/ML: Scikit-learn, Pandas, NumPy

Backend: FastAPI, Docker, Uvicorn

Frontend: Streamlit, Plotly

Database: PostgreSQL, SQLAlchemy

Cloud: Render, Neon, Streamlit Cloud

## 🚀 Deployment Links
Live Dashboard: [https://axon-predictive-engine.streamlit.app/](https://axon-predictive-engine.streamlit.app/)

API Documentation (Swagger): [https://axon-predictive-engine-1.onrender.com/docs](https://axon-predictive-engine-1.onrender.com/docs)

## 📂 Project Structure
src/: Contains the core logic.

app.py: FastAPI Backend & AI Logic

dashboard.py: Streamlit UI & Data Visualization

models/: Trained Scikit-learn model files

Dockerfile: Backend containerization settings.

requirements.txt: Python dependencies.

vercel.json: Configuration for frontend routing.


## 💻 How to Run Locally
Clone the repo: git clone [https://github.com/Chandann-23/AXON-Predictive-Engine.git](https://github.com/Chandann-23/AXON-Predictive-Engine.git)

Set up Environment Variables: Create a .env file with your DATABASE_URL.

## Run with Docker:

docker build -t axon-backend .

docker run -p 10000:10000 axon-backend