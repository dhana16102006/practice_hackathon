# app.py
import streamlit as st
from datetime import datetime
import random
from agents.risk_agent import classify_risk
from agents.alert_agent import create_alert
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FactoryGuardian Dashboard", layout="wide")

# --- Auto-refresh every 3 seconds ---
st_autorefresh(interval=3000, key="factory_dashboard")

# --- Session state ---
if 'LATEST_READINGS' not in st.session_state:
    st.session_state['LATEST_READINGS'] = {}
if 'ALERTS' not in st.session_state:
    st.session_state['ALERTS'] = {}

MACHINES = ["M1", "M2", "M3", "M4"]

# --- Animated Gradient Header ---
st.markdown("""
<div style="text-align:center; padding:40px 20px;">
    <h1 style="
        font-size:80px; font-weight:900;
        background: linear-gradient(270deg, #00bfff, #ff6f61, #ffb347, #6a5acd);
        background-size: 800% 800%;
        -webkit-background-clip: text; color: transparent;
        animation: gradientAnimation 8s ease infinite;
        text-shadow: 2px 2px 15px rgba(0,0,0,0.2);
    ">MACHINE GUARD</h1>
    <p style="
        font-size:26px; font-weight:bold;
        background: linear-gradient(270deg, #1e90ff, #ff69b4, #ffd700, #00ff7f);
        background-size: 800% 800%;
        -webkit-background-clip: text; color: transparent;
        animation: gradientAnimation 6s ease infinite;
        text-shadow: 1px 1px 12px rgba(0,0,0,0.2);
    ">Smart Monitoring System for Factories</p>
</div>
<style>
@keyframes gradientAnimation {
    0%{background-position:0% 50%}
    50%{background-position:100% 50%}
    100%{background-position:0% 50%}
}
</style>
""", unsafe_allow_html=True)

# --- Simulate readings ---
def simulate_readings():
    for m in MACHINES:
        reading = {
            "temperature": round(random.uniform(20, 110), 2),
            "vibration": round(random.uniform(0.0, 4.5), 2),
            "gas_level": round(random.uniform(0.0, 20.0), 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        risk = classify_risk(reading).get("risk_level", "normal")
        reading["risk_level"] = risk
        st.session_state['LATEST_READINGS'][m] = reading

        if risk == "critical":
            alert = create_alert(m, reading, {"risk_level": risk})
            st.session_state['ALERTS'][m] = alert

simulate_readings()

# --- Machine Cards ---
st.markdown("## 🌟 Machine Readings", unsafe_allow_html=True)
cols = st.columns(len(MACHINES))

for i, machine in enumerate(MACHINES):
    data = st.session_state['LATEST_READINGS'][machine]
    risk = data.get("risk_level", "normal")
    color_map = {
        "normal": "linear-gradient(135deg, #6a11cb, #2575fc)",
        "warning": "linear-gradient(135deg, #f7971e, #ffd200)",
        "critical": "linear-gradient(135deg, #ff416c, #ff4b2b)"
    }
    color = color_map.get(risk, "linear-gradient(135deg, #6a11cb, #2575fc)")

    with cols[i]:
        st.markdown(f"""
        <div style="
            padding:25px; border-radius:20px; margin:10px;
            background: {color};
            box-shadow: 0 15px 40px rgba(0,0,0,0.25);
            position: relative; overflow:hidden;
            min-height:320px;
            transition: transform 0.4s, box-shadow 0.4s;
        " onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 25px 60px rgba(0,0,0,0.35)';"
           onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 15px 40px rgba(0,0,0,0.25)';">
            <h2 style='color:white; font-size:28px; font-weight:bold; text-shadow:1px 1px 10px rgba(0,0,0,0.3);'>{machine}</h2>
            <p>🌡️ Temp: <b>{data.get('temperature','-')} °C</b></p>
            <p>📳 Vibration: <b>{data.get('vibration','-')}</b></p>
            <p>🧪 Gas: <b>{data.get('gas_level','-')}</b></p>
            <p>⚡ Risk Level: <b>{risk.upper()}</b></p>
            <small>⏱ {data.get('timestamp','')}</small>
        </div>
        """, unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=data.get('temperature', 0),
            title={'text': "Temp °C"},
            gauge={'axis': {'range': [0, 120]},
                   'bar': {'color': '#ffffff'},
                   'steps': [
                       {'range': [0, 70], 'color': "#6a11cb"},
                       {'range': [70, 90], 'color': "#f7971e"},
                       {'range': [90, 120], 'color': "#ff416c"}]}
        ))
        fig.update_layout(height=180, margin=dict(t=0, b=0, l=0, r=0),
                          paper_bgcolor='rgba(0,0,0,0)', font=dict(color='black'))
        st.plotly_chart(fig, use_container_width=True)

# --- Live Alerts ---
st.markdown("## 🚨 Live Alerts", unsafe_allow_html=True)
for alert in st.session_state['ALERTS'].values():
    st.markdown(f"""
        <div style="
            padding:15px; margin-bottom:10px; border-radius:15px;
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        ">
            <b>{alert['machine_id']}</b>: {alert['message']}<br>
            <small>{alert['timestamp']}</small>
        </div>
    """, unsafe_allow_html=True)
