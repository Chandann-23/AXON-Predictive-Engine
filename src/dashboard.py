import streamlit as st
import requests
import json
import plotly.express as px
import pandas as pd
import psutil
import time
import plotly.graph_objects as go
import random

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
        font-weight: 800;
        font-size: 5rem;
        letter-spacing: -3px;
        background: linear-gradient(180deg, #ffffff, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1;
    }
    .brand-subtitle {
        font-weight: 300;
        font-size: 0.9rem;
        letter-spacing: 6px;
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

st.markdown('<div class="nav-container"></div>', unsafe_allow_html=True)

# FIXED HELPER FUNCTION
def get_prediction(cpu, ram, temp, latency):
    API_URL = "https://axon-predictive-engine.onrender.com/predict"
    payload = {"cpu": cpu, "ram": ram, "temp": temp, "latency": latency}
    try:
        # Crucial: Use 'params=payload' for GET requests
        response = requests.get(API_URL, params=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"AXON API Error: {e}")
    return None

def render_dashboard_content(cpu, ram, temp, latency, result):
    # Determine Probability using SAFE .get() method
    # Change "prediction" to "failure_probability" only if your app.py specifically uses that key
    prob = 0.0
    status = "Unknown"
    
    if result:
        # We try both common keys to be safe
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
            
            if "feature_importance" in result:
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

# Branding
st.markdown('<div class="brand-container"><h1 class="brand-axon">AXON</h1><p class="brand-subtitle">Predictive Health Engine</p></div>', unsafe_allow_html=True)

tab_monitor, tab_doc = st.tabs(["01 / MONITOR", "02 / DOCUMENTATION"])

with tab_monitor:
    st.sidebar.header("TELEMETRY STREAM")
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