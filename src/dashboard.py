import streamlit as st
import requests
import json
import plotly.express as px
import pandas as pd
import psutil
import time
import plotly.graph_objects as go
import random
import numpy as np

# Page configuration
st.set_page_config(
    page_title="AXON Predictive Engine",
    page_icon="🖥️",
    layout="wide"
)

# Custom CSS for high-tech SaaS UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fixed Navbar Styling */
    .nav-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 70px;
        background: rgba(14, 17, 23, 0.7);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 50px;
        z-index: 1000;
    }
    
    .stApp {
        padding-top: 80px;
    }

    [data-testid="stSidebar"] {
        background-color: #0e1117;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Centered Branding */
    .brand-container {
        text-align: center;
        padding: 40px 0 20px 0;
    }
    .brand-axon {
        font-weight: 900;
        font-size: 5rem;
        letter-spacing: -3px;
        background: linear-gradient(180deg, #ffffff, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1;
        text-shadow: 0px 0px 20px rgba(0, 212, 255, 0.5);
    }
    .brand-subtitle {
        font-weight: 300;
        font-size: 1.2rem;
        letter-spacing: 12px;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 10px;
        text-transform: uppercase;
    }
    
    /* Pulsing LED */
    .led-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    .led-circle {
        width: 20px;
        height: 20px;
        border-radius: 50%;
    }
    .led-green { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
    .led-red { 
        background-color: #ff0000; 
        box-shadow: 0 0 10px #ff0000; 
        animation: pulse-red 1s infinite alternate; 
    }
    @keyframes pulse-red {
        from { opacity: 0.8; } to { opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'prev_cpu' not in st.session_state: st.session_state.prev_cpu = 50.0
if 'prev_ram' not in st.session_state: st.session_state.prev_ram = 50.0
if 'history' not in st.session_state: st.session_state.history = []
if 'telemetry_history' not in st.session_state: st.session_state.telemetry_history = []
if 'last_result' not in st.session_state: st.session_state.last_result = None
if 'inference_latency' not in st.session_state: st.session_state.inference_latency = 0.0

st.markdown('<div class="nav-container"></div>', unsafe_allow_html=True)

# FIXED HELPER FUNCTION
def get_prediction(cpu, ram, temp, latency):
    API_URL = "https://axon-predictive-engine.onrender.com/predict"
    payload = {"cpu": cpu, "ram": ram, "temp": temp, "latency": latency}
    start_time = time.time()
    try:
        response = requests.get(API_URL, params=payload, timeout=5)
        st.session_state.inference_latency = (time.time() - start_time) * 1000 # in ms
        if response.status_code == 200:
            result = response.json()
            st.session_state.last_result = result
            return result
    except Exception as e:
        print(f"AXON API Error: {e}")
    return None

def report_false_positive(cpu, ram, temp, latency):
    API_URL = "https://axon-predictive-engine.onrender.com/feedback"
    payload = {
        "cpu": cpu,
        "ram": ram,
        "temp": temp,
        "latency": latency,
        "label": "false_positive"
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Feedback Error: {e}")
        return False

def check_api_health():
    HEALTH_URL = "https://axon-predictive-engine.onrender.com/" # Assuming base URL is health check
    try:
        response = requests.get(HEALTH_URL, timeout=3)
        return response.status_code == 200
    except:
        return False

def get_history_data():
    HISTORY_URL = "https://axon-predictive-engine.onrender.com/history"
    try:
        response = requests.get(HISTORY_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"History Fetch Error: {e}")
    return []

def render_dashboard_content(cpu, ram, temp, latency, result):
    # Determine Probability using SAFE .get() method
    prob = 0.0
    status = "Unknown"
    
    if result:
        prob = result.get("failure_probability", 0.0) 
        status = result.get("status", "STABLE")

        led_class = "led-red" if prob > 0.8 else "led-green"
        led_text = "CRITICAL RISK" if prob > 0.8 else "SYSTEM STABLE"
        
        st.markdown(f"""
            <div class="led-container">
                <div class="led-circle {led_class}"></div>
                <span style="font-weight: 800; font-size: 0.9rem; color: rgba(255,255,255,0.8);">{led_text}</span>
            </div>
        """, unsafe_allow_html=True)

        # Update Telemetry History
        timestamp = time.strftime("%H:%M:%S")
        st.session_state.telemetry_history.append({
            "timestamp": timestamp,
            "failure_probability": prob * 100
        })
        st.session_state.telemetry_history = st.session_state.telemetry_history[-30:]

    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("🛡️ AI System Health Gauge")
        if result:
            color = "#00ff00" if prob <= 0.4 else ("#ffa500" if prob <= 0.7 else "#ff4b4b")
            st.markdown(f"""
                <div class="glass-card">
                    <div style="background-color: {color}; padding: 30px; border-radius: 12px; text-align: center; color: white;">
                        <h2 style="margin:0;">{status.upper()}</h2>
                        <h1 style="font-size: 5em; margin:15px 0;">{prob*100:.1f}%</h1>
                        <p style="margin:0; opacity: 0.8;">PROBABILITY OF FAILURE</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Feedback Button
            if st.button("🚫 Report False Positive", use_container_width=True):
                if report_false_positive(cpu, ram, temp, latency):
                    st.success("Feedback recorded. Thank you!")
                else:
                    st.error("Failed to send feedback.")

            if "feature_importance" in result:
                st.subheader("🔍 Dynamic Risk Drivers")
                fi_data = result["feature_importance"]
                df_fi = pd.DataFrame({"Feature": list(fi_data.keys()), "Importance": list(fi_data.values())}).sort_values(by="Importance")
                fig_fi = px.bar(df_fi, x="Importance", y="Feature", orientation='h', color_discrete_sequence=['#00d4ff'])
                fig_fi.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=250)
                st.plotly_chart(fig_fi, use_container_width=True)
        else:
            st.warning("📡 AI Engine Synchronizing... (Render may take 60s to wake up)")

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("⚡ Live System Telemetry")
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("CPU", f"{cpu:.1f}%", delta=f"{cpu - st.session_state.prev_cpu:.1f}%")
        m_col2.metric("RAM", f"{ram:.1f}%", delta=f"{ram - st.session_state.prev_ram:.1f}%")
        st.metric("TEMP", f"{temp:.1f}°C")
        st.metric("LATENCY", f"{latency:.1f}ms")
        st.markdown('</div>', unsafe_allow_html=True)

    # 📈 Global Risk Trajectory & AI Predictive Horizon
    st.markdown("---")
    st.subheader("📈 Global Risk Trajectory & AI Predictive Horizon", 
                 help="This represents the expected system stress if current telemetry trends continue.")
    
    # Fetch data from Database instead of session state
    db_history = get_history_data()
    
    if db_history:
        # Convert to DataFrame and sort by timestamp ascending for plotting
        df_hist = pd.DataFrame(db_history)
        df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'])
        df_hist = df_hist.sort_values('timestamp')
        
        # Format timestamp for display
        df_hist['display_time'] = df_hist['timestamp'].dt.strftime('%H:%M:%S')
        
        # Base historical chart
        fig_hist = go.Figure()
        
        # Historical Trace
        fig_hist.add_trace(go.Scatter(
            x=df_hist["display_time"], 
            y=df_hist["failure_probability"] * (100 if df_hist["failure_probability"].max() <= 1 else 1),
            mode='lines+markers',
            name='Historical Risk',
            line=dict(color='#00d4ff', width=3),
            marker=dict(size=6)
        ))
        
        # AI Predictive Horizon Forecasting
        if len(df_hist) > 10:
            # Handle potential scaling differences (API returns decimal, dashboard uses percentage)
            y_vals = df_hist["failure_probability"].values
            if y_vals.max() <= 1.0:
                y_vals = y_vals * 100
                
            x = np.arange(len(y_vals))
            
            # Simple linear trend (slope and intercept)
            m, b = np.polyfit(x, y_vals, 1)
            
            # Forecast next 5 points
            x_forecast = np.arange(len(y_vals), len(y_vals) + 5)
            y_forecast = m * x_forecast + b
            y_forecast = np.clip(y_forecast, 0, 100) # Keep within 0-100%
            
            # Forecast labels (e.g., Last, T+1, T+2...)
            last_timestamp = df_hist["display_time"].iloc[-1]
            forecast_labels = [last_timestamp] + [f"T+{i+1}" for i in range(5)]
            
            # Include last point for continuity
            y_forecast_continuous = np.concatenate(([y_vals[-1]], y_forecast))
            
            # Add Predicted Path Trace
            fig_hist.add_trace(go.Scatter(
                x=forecast_labels,
                y=y_forecast_continuous,
                mode='lines',
                name='Predicted Path',
                line=dict(color='#00d4ff', width=2, dash='dash'),
                hovertemplate="<b>%{x}</b>: %{y:.1f}% Risk"
            ))
            
            st.caption(f"✨ **AI Predictive Horizon**: Linear projection based on last {len(df_hist)} samples from DB.")

        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            font_color="white", 
            height=400, 
            yaxis_range=[0, 100],
            xaxis_title="Time of Telemetry (IST)",
            yaxis_title="Risk (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Waiting for historical telemetry data from AXON Database...")

    # Update previous values for next delta calculation
    st.session_state.prev_cpu = cpu
    st.session_state.prev_ram = ram


# Branding
st.markdown('<div class="brand-container"><h1 class="brand-axon">AXON</h1><p class="brand-subtitle">Predictive Health Engine</p></div>', unsafe_allow_html=True)

tab_monitor, tab_doc, tab_mlops = st.tabs(["01 / MONITOR", "02 / DOCUMENTATION", "03 / MLOPS"])

with tab_monitor:
    st.sidebar.header("TELEMETRY STREAM")
    
    # Export History Button
    db_history = get_history_data()
    if db_history:
        # Last Sync Display
        latest_entry = db_history[0]
        latest_ts = pd.to_datetime(latest_entry['timestamp']).strftime('%H:%M:%S')
        st.sidebar.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background: rgba(0, 212, 255, 0.1); border: 1px solid rgba(0, 212, 255, 0.2); margin-bottom: 20px;">
                <p style="margin:0; font-size: 0.8rem; color: #00d4ff; font-weight: 600;">Last AI Pulse: {latest_ts}</p>
            </div>
        """, unsafe_allow_html=True)

        df_export = pd.DataFrame(db_history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Export History",
            data=csv,
            file_name=f"axon_history_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    
    live_mode = st.sidebar.toggle("ACTIVATE LIVE FEED", value=False)

    if not live_mode:
        cpu = st.sidebar.slider("CPU Usage (%)", 0.0, 100.0, 50.0)
        ram = st.sidebar.slider("RAM Usage (%)", 0.0, 100.0, 50.0)
        temp = st.sidebar.slider("Temp (°C)", 0.0, 120.0, 45.0)
        latency = st.sidebar.slider("Latency (ms)", 0.0, 500.0, 50.0)
        result = get_prediction(cpu, ram, temp, latency)
        render_dashboard_content(cpu, ram, temp, latency, result)
    else:
        # Live Logic
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        temp = random.uniform(40, 60) # Fallback for temp
        result = get_prediction(cpu, ram, temp, 20.0)
        render_dashboard_content(cpu, ram, temp, 20.0, result)
        time.sleep(2)
        st.rerun()

with tab_doc:
    st.info("Documentation: AXON utilizes a Random Forest model hosted on Render via FastAPI.")

with tab_mlops:
    st.header("🛠️ MLOps Lifecycle Control")
    
    st.subheader("System Health")
    m_col1, m_col2, m_col3 = st.columns(3)
    
    # Column 1: Inference Latency
    m_col1.metric("Inference Latency", f"{st.session_state.inference_latency:.2f} ms")
    
    # Column 2: API Status
    is_online = check_api_health()
    status_text = "ONLINE" if is_online else "OFFLINE"
    status_color = "green" if is_online else "red"
    m_col2.metric("API Status", status_text, delta=None, delta_color="normal")
    
    # Column 3: Model Version
    m_col3.metric("Model Version", "v1.0.2", help="Algorithm: Random Forest")

    # JSON Debugger
    st.markdown("---")
    st.subheader("🔍 API Inspector (Last Raw Response)")
    if st.session_state.last_result:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.json(st.session_state.last_result)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No API response captured yet. Interact with the Monitor tab to trigger a call.")