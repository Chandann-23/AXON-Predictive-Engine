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
    page_title="Server Health Dashboard",
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
    .logo-container {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 800;
        font-size: 1.2rem;
        color: #00d4ff;
    }
    
    /* Content Padding for Fixed Nav */
    .stApp {
        padding-top: 80px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Glassmorphism Card Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    /* Minimalist Tab Styling */
    button[data-testid="stBaseButton-tab"] {
        border: none !important;
        background: transparent !important;
        color: rgba(255, 255, 255, 0.4) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 1.5px !important;
        padding: 10px 20px !important;
    }
    
    button[data-testid="stBaseButton-tab"][aria-selected="true"] {
        color: #00d4ff !important;
        border-bottom: 2px solid #00d4ff !important;
        box-shadow: 0 10px 15px -5px rgba(0, 212, 255, 0.2) !important;
    }

    button[data-testid="stBaseButton-tab"]:hover {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Disappear effect for empty containers */
    .glass-card:empty {
        display: none;
        border: none;
    }
    
    /* Glowing Metric Logic */
    .metric-glow-healthy {
        text-shadow: 0 0 10px rgba(0, 255, 0, 0.4);
        color: #00ff00 !important;
    }
    
    /* Main Title Styling */
    .main-title {
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #00d4ff, #00ff00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
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
        filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.3));
    }
    .brand-subtitle {
        font-weight: 300;
        font-size: 0.9rem;
        letter-spacing: 6px;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 10px;
        text-transform: uppercase;
    }
    
    /* Pulsing LED CSS */
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
    .led-green {
        background-color: #00ff00;
        box-shadow: 0 0 10px #00ff00;
    }
    .led-red {
        background-color: #ff0000;
        box-shadow: 0 0 10px #ff0000;
        animation: pulse-red 1s infinite alternate;
    }
    @keyframes pulse-red {
        from { box-shadow: 0 0 5px #ff0000; opacity: 0.8; }
        to { box-shadow: 0 0 25px #ff0000; opacity: 1; }
    }
    
    </style>
""", unsafe_allow_html=True)

# Initialize session state for deltas and history
if 'prev_cpu' not in st.session_state:
    st.session_state.prev_cpu = 50.0
if 'prev_ram' not in st.session_state:
    st.session_state.prev_ram = 50.0
if 'history' not in st.session_state:
    st.session_state.history = []

# Navigation Bar (Empty for Minimalism or hidden)
st.markdown('<div class="nav-container"></div>', unsafe_allow_html=True)

# Helper Functions
def get_prediction(cpu, ram, temp, latency):
    API_URL = "https://axon-predictive-engine.onrender.com/predict"
    # We must define the payload here so the function knows what to send!
    payload = {
        "cpu": cpu, 
        "ram": ram, 
        "temp": temp, 
        "latency": latency
    }
    try:
        # Changed 'input_data' to 'payload'
        # Use GET and 'params'
        response = requests.get(API_URL, params=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        # This will print to your Streamlit logs so you can see it
        print(f"AXON Connection Error: {e}")
    return None

def render_dashboard_content(cpu, ram, temp, latency, result):
    # Pulsing LED Status Component
    if result:
        prob = result["failure_probability"]
        led_class = "led-red" if prob > 0.8 else "led-green"
        led_text = "CRITICAL RISK" if prob > 0.8 else "SYSTEM STABLE"
        
        st.markdown(f"""
            <div class="led-container">
                <div class="led-circle {led_class}"></div>
                <span style="font-weight: 800; font-size: 0.9rem; color: rgba(255,255,255,0.8);">{led_text}</span>
            </div>
        """, unsafe_allow_html=True)

    # Layout for results
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("🛡️ AI System Health Gauge")
        gauge_spot = st.empty()
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔍 Dynamic Risk Drivers")
        fi_spot = st.empty()
        
        if result:
            prob = result["failure_probability"]
            status = result["status"]
            color = "#00ff00" if prob <= 0.4 else ("#ffa500" if prob <= 0.7 else "#ff4b4b")
            
            with gauge_spot.container():
                st.markdown(f'<div class="glass-card"><div style="background-color: {color}; padding: 30px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 10px 30px {color}33;"><h2 style="margin:0; font-weight: 800;">{status.upper()}</h2><h1 style="font-size: 5em; margin:15px 0; font-weight: 800;">{prob*100:.1f}%</h1><p style="margin:0; opacity: 0.8; font-weight: 600;">PROBABILITY OF FAILURE</p></div></div>', unsafe_allow_html=True)

            if "feature_importance" in result:
                fi_data = result["feature_importance"]
                df_fi = pd.DataFrame({"Feature": list(fi_data.keys()), "Importance": list(fi_data.values())}).sort_values(by="Importance", ascending=True)
                fig_fi = px.bar(df_fi, x="Importance", y="Feature", orientation='h', color="Importance", color_continuous_scale="Viridis")
                fig_fi.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0), height=250, showlegend=False, coloraxis_showscale=False, font_color="white", xaxis_showgrid=False, yaxis_showgrid=False)
                with fi_spot.container():
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.plotly_chart(fig_fi, use_container_width=True, key=f"fi_chart_{time.time()}")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            st.session_state.history.append({"Reading": time.strftime("%H:%M:%S"), "Probability": prob * 100})
            st.session_state.history = st.session_state.history[-50:]
        else:
            with gauge_spot.container(): st.warning("📡 AI Engine Synchronizing...")
            with fi_spot.container(): st.info("Waiting for telemetry analysis...")

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("⚡ Live System Telemetry")
        cpu_delta = cpu - st.session_state.prev_cpu
        ram_delta = ram - st.session_state.prev_ram
        cpu_glow = "metric-glow-healthy" if cpu < 60 else ""
        ram_glow = "metric-glow-healthy" if ram < 70 else ""
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown(f'<div class="{cpu_glow}">', unsafe_allow_html=True)
            st.metric("CPU UTILIZATION", f"{cpu:.1f}%", delta=f"{cpu_delta:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f'<div class="{ram_glow}">', unsafe_allow_html=True)
            st.metric("RAM UTILIZATION", f"{ram:.1f}%", delta=f"{ram_delta:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<hr style='border: 0.5px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.metric("SYSTEM TEMPERATURE", f"{temp:.1f}°C")
        st.metric("NETWORK LATENCY", f"{latency:.1f}ms")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("⚖️ System Balance View")
        radar_cpu, radar_ram = cpu, ram
        radar_temp, radar_latency = (temp / 120.0) * 100, (latency / 500.0) * 100
        fig_radar = go.Figure(go.Scatterpolar(r=[radar_cpu, radar_ram, radar_temp, radar_latency], theta=['CPU', 'RAM', 'TEMP', 'LATENCY'], fill='toself', line_color='#00d4ff', fillcolor='rgba(0, 212, 255, 0.3)'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor='rgba(255,255,255,0.1)'), angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', linecolor='rgba(255,255,255,0.1)')), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=40, b=40), height=300, font_color="white")
        st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_chart_{time.time()}")
        st.session_state.prev_cpu, st.session_state.prev_ram = cpu, ram
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("📈 Global Risk Trajectory (Last 50 Samples)")
    history_spot = st.empty()
    if st.session_state.history:
        df_history = pd.DataFrame(st.session_state.history)
        fig = px.line(df_history, x="Reading", y="Probability", range_y=[0, 100], markers=True, labels={"Probability": "Risk Level (%)", "Reading": "Timestamp"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=30), height=350, font_color="white", xaxis_showgrid=False, yaxis_showgrid=True, yaxis_gridcolor="rgba(255,255,255,0.05)")
        with history_spot.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, key=f"risk_chart_{time.time()}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with history_spot.container(): st.info("AI Analysis History Initializing...")

@st.fragment(run_every=2)
def live_update_fragment():
    live_cpu, live_ram = psutil.cpu_percent(interval=None), psutil.virtual_memory().percent
    try:
        temps = psutil.sensors_temperatures()
        live_temp = temps['coretemp'][0].current if temps and 'coretemp' in temps else random.uniform(40.0, 60.0)
    except:
        live_temp = random.uniform(40.0, 60.0)
    prediction_data = get_prediction(live_cpu, live_ram, live_temp, 20.0)
    with st.container(): render_dashboard_content(live_cpu, live_ram, live_temp, 20.0, prediction_data)

# Centered Branding Header
st.markdown("""
    <div class="brand-container">
        <h1 class="brand-axon">AXON</h1>
        <p class="brand-subtitle">Predictive Health Engine</p>
    </div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_monitor, tab_doc = st.tabs(["01 / MONITOR", "02 / DOCUMENTATION"])

with tab_monitor:
    # Sidebar for inputs (Scoped to Monitor)
    st.sidebar.header("TELEMETRY STREAM")
    live_mode = st.sidebar.toggle("ACTIVATE LIVE FEED", value=False)

    if not live_mode:
        cpu = st.sidebar.slider("CPU Usage (%)", 0.0, 100.0, 50.0, step=0.1)
        ram = st.sidebar.slider("RAM Usage (%)", 0.0, 100.0, 50.0, step=0.1)
        temp = st.sidebar.slider("Temperature (°C)", 0.0, 120.0, 45.0, step=0.1)
        latency = st.sidebar.slider("Network Latency (ms)", 0.0, 500.0, 50.0, step=1.0)
        result = get_prediction(cpu, ram, temp, latency)
        render_dashboard_content(cpu, ram, temp, latency, result)
    else:
        st.sidebar.info("📡 Live Telemetry Active")
        live_update_fragment()

with tab_doc:
    st.markdown("""
    <div class="glass-card">
    <h3 style="color: #00d4ff; letter-spacing: 1px;">I. System Architecture</h3>
    <p style="opacity: 0.8;">AXON operates on a <strong>Decoupled Microservice Architecture</strong>. The frontend acts as a telemetry harvester, while the backend serves as a high-concurrency inference engine.</p>
    </div>
    
    <div class="glass-card">
    <h3 style="color: #00d4ff; letter-spacing: 1px;">II. The Neural Core</h3>
    <p style="opacity: 0.8;"><strong>Algorithm:</strong> Random Forest Ensemble.</p>
    <p style="opacity: 0.8;"><strong>Reasoning:</strong> Unlike linear thresholds, AXON analyzes the <em>Entropy</em> between CPU load and thermal spikes. It identifies 'System Stress Signatures' that a human observer would miss.</p>
    <p style="opacity: 0.8; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;">
        Pipeline: Data Ingestion (psutil) &rarr; Feature Vectorization &rarr; REST API Call (FastAPI) &rarr; Prediction
    </p>
    </div>
    
    <div class="glass-card">
    <h3 style="color: #00d4ff; letter-spacing: 1px;">III. Deployment</h3>
    <p style="opacity: 0.8;">The entire stack is <strong>Containerized via Docker</strong>, ensuring that the 'Neural Core' remains immutable across different hardware environments.</p>
    </div>
    """, unsafe_allow_html=True)
