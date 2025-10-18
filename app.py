# app.py
import streamlit as st
from datetime import datetime
import random
from agents.risk_agent import classify_risk
from agents.alert_agent import create_alert
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Dashboard", layout="wide")


st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(120deg, #141e30, #243b55);
            /* OR: background-color: #232323;  For solid color */
        }
        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);  /* make top header transparent if you want */
        }
    </style>
    """,
    unsafe_allow_html=True
)



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





# --- 🔊 Enable Alarm Sound (User gesture for autoplay) ---
if 'AUDIO_ENABLED' not in st.session_state:
    st.session_state['AUDIO_ENABLED'] = False

# If not enabled, show button and stop rest of app
if not st.session_state['AUDIO_ENABLED']:
    if st.button("🔊 Enable Alarm Sound"):
        st.session_state['AUDIO_ENABLED'] = True
    st.stop()  # Stop rendering the rest of the app until user clicks







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




# --- 🔔 Alarm on Critical Alerts (via URL) ---
def play_alarm_url(url):
    audio_html = f"""
    <div id="alarm_container">
      <audio id="alarm" autoplay loop>
        <source src="{url}" type="audio/mpeg">
        Your browser does not support the audio element.
      </audio>
      <div style="margin-top:8px;">
        <button onclick="document.getElementById('alarm').pause()">Mute / Pause</button>
        <button onclick="document.getElementById('alarm').play()">Play</button>
      </div>
    </div>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Only trigger alarm if AUDIO_ENABLED is True
if st.session_state.get('AUDIO_ENABLED', False):
    critical_found = any(
        r.get("risk_level") == "critical"
        for r in st.session_state['LATEST_READINGS'].values()
    )

    if critical_found and not st.session_state.get('ALARM_ACTIVE', False):
        st.session_state['ALARM_ACTIVE'] = True
        alarm_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        play_alarm_url(alarm_url)

# Stop/Acknowledge Alarm Button
if st.session_state.get('ALARM_ACTIVE', False):
    if st.button("Acknowledge & Stop Alarm"):
        stop_js = """
        <script>
        var a = document.getElementById('alarm');
        if(a){ a.pause(); a.currentTime = 0; }
        var c = document.getElementById('alarm_container');
        if(c){ c.remove(); }
        </script>
        """
        st.markdown(stop_js, unsafe_allow_html=True)
        st.session_state['ALARM_ACTIVE'] = False







  
# -------------------------
# >>> ADD-ON: History, Chart, AI Insights
# Paste this block RIGHT AFTER the call to simulate_readings() and BEFORE your "Machine Cards" block.
# -------------------------

# --- preserve short history (no change to existing functions) ---
if 'HISTORY' not in st.session_state:
    # store up to N recent readings per machine
    st.session_state['HISTORY'] = {m: [] for m in MACHINES}
if 'MAX_HISTORY' not in st.session_state:
    st.session_state['MAX_HISTORY'] = 20

# Append latest readings into HISTORY (called once per refresh, non-destructive)
for m in MACHINES:
    latest = st.session_state['LATEST_READINGS'].get(m)
    if latest:
        hist = st.session_state['HISTORY'].get(m, [])
        # create a compact entry
        entry = {
            "timestamp": latest.get("timestamp", datetime.utcnow().isoformat()),
            "temperature": latest.get("temperature"),
            "vibration": latest.get("vibration"),
            "gas_level": latest.get("gas_level"),
            "risk_level": latest.get("risk_level", "normal")
        }
        # avoid duplicate consecutive identical timestamps (in case autorefresh triggered twice quickly)
        if not hist or hist[-1].get("timestamp") != entry["timestamp"]:
            hist.append(entry)
        # trim to MAX_HISTORY
        max_h = st.session_state['MAX_HISTORY']
        if len(hist) > max_h:
            hist = hist[-max_h:]
        st.session_state['HISTORY'][m] = hist

# --- Real-time Temperature Line Chart across machines (Plotly) ---
st.markdown("## 📈 Sensor Simulation — Temperature Over Time", unsafe_allow_html=True)

# Build a time-aligned X axis by using the union of timestamps present in histories (simple approach)
all_timestamps = []
for m in MACHINES:
    for e in st.session_state['HISTORY'].get(m, []):
        if e['timestamp'] not in all_timestamps:
            all_timestamps.append(e['timestamp'])
# sort timestamps for x-axis ordering
all_timestamps = sorted(all_timestamps)

# convert ISO timestamps to readable labels (HH:MM:SS)
def iso_to_label(ts):
    try:
        return datetime.fromisoformat(ts).strftime("%H:%M:%S")
    except Exception:
        return ts

x_labels = [iso_to_label(t) for t in all_timestamps]

fig_temp = go.Figure()
for m in MACHINES:
    # create a mapping timestamp->value for the machine's history
    hist_map = {e['timestamp']: e['temperature'] for e in st.session_state['HISTORY'].get(m, [])}
    # build y values aligned to all_timestamps (use None when missing)
    ys = [hist_map.get(ts, None) for ts in all_timestamps]
    fig_temp.add_trace(go.Scatter(
        x=x_labels,
        y=ys,
        mode='lines+markers',
        name=m,
        connectgaps=True,
        line=dict(width=2),
    ))

fig_temp.update_layout(
    height=360,
    margin=dict(t=20, b=40, l=40, r=20),
    xaxis_title="Time (UTC)",
    yaxis_title="Temperature (°C)",
    legend_title="Machine",
    template='plotly_white'
)

st.plotly_chart(fig_temp, use_container_width=True)

# --- AI Insights Panel (summary + simple heuristics) ---
st.markdown("##  AI Insights (Summary & Suggestions)", unsafe_allow_html=True)

def generate_ai_insights_simple(latest_readings, history, machines):
    """
    Lightweight insights generator. Replace with LLM call where appropriate.
    Returns dict with 'summary' and 'recommendations'.
    """
    temps = []
    vib = []
    gas = []
    critical = []
    warning = []
    spikes = []

    for m in machines:
        r = latest_readings.get(m)
        if not r:
            continue
        temps.append(r['temperature'])
        vib.append(r['vibration'])
        gas.append(r['gas_level'])
        if r.get('risk_level') == 'critical':
            critical.append(m)
        elif r.get('risk_level') == 'warning':
            warning.append(m)

        # check short-term spike in history
        h = history.get(m, [])
        if len(h) >= 2:
            prev = h[-2]['temperature']
            last = h[-1]['temperature']
            if last is not None and prev is not None and (last - prev) > 8:
                spikes.append(f"{m}: {prev}→{last}°C")

    avg_temp = round(sum(temps)/len(temps),2) if temps else None
    max_temp = round(max(temps),2) if temps else None
    avg_vib = round(sum(vib)/len(vib),2) if vib else None
    max_gas = round(max(gas),2) if gas else None

    summary = []
    if avg_temp is not None:
        summary.append(f"Average temperature: {avg_temp} °C")
    if max_temp is not None:
        summary.append(f"Max temperature: {max_temp} °C")
    if avg_vib is not None:
        summary.append(f"Average vibration: {avg_vib} mm/s")
    if critical:
        summary.append(f"CRITICAL machines: {', '.join(critical)}")
    elif warning:
        summary.append(f"Warning-level machines: {', '.join(warning)}")
    else:
        summary.append("No immediate critical risks detected.")

    if spikes:
        summary.append("Temperature spikes detected: " + "; ".join(spikes))

    recs = []
    if max_temp and max_temp > 95:
        recs.append("Immediate inspection recommended for machines >95°C.")
    if avg_vib and avg_vib > 3.0:
        recs.append("High average vibration — inspect mounts/bearings.")
    if max_gas and max_gas > 15:
        recs.append("Elevated gas — verify ventilation and sensors.")

    if not recs:
        recs.append("Continue monitoring; consider capturing higher-frequency telemetry during stress windows.")

    return {"summary": summary, "recs": recs}

insights = generate_ai_insights_simple(st.session_state['LATEST_READINGS'], st.session_state['HISTORY'], MACHINES)

# Display insights in two columns
c1, c2 = st.columns([3,1])
with c1:
    st.markdown("<div style='padding:12px; border-radius:10px; background:#f7f9fb;'>", unsafe_allow_html=True)
    st.markdown("**Summary:**")
    for s in insights['summary']:
        st.markdown(f"- {s}")
    st.markdown("**Recommendations:**")
    for r in insights['recs']:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div style='padding:12px; border-radius:10px; background:#ffffff; box-shadow:0 8px 20px rgba(0,0,0,0.06);'>", unsafe_allow_html=True)
    st.markdown("**AI Actions**")
    
    if st.button("Run LLM Insights (mock)"):
        # This is a mock response. Replace with real Mistral code if desired.
        st.info("Running LLM (mock) — sending compact summary to model...")
        example_prompt = {
            "summary": insights['summary'],
            "recent_history_sample": {m: st.session_state['HISTORY'].get(m, [])[-5:] for m in MACHINES}
        }
        # show the prompt we would send (compact)
        st.code(example_prompt, language='json')
        # Simulated LLM reply
        st.success("LLM (mock) response:")
        st.write("Suggested: Prioritise M4 for a maintenance check. Increase sampling to 1s for M4 for 10 minutes during the next stress window.")
    st.markdown("</div>", unsafe_allow_html=True)

# End of add-on block
# -------------------------gs()















# --- Machine Cards ---
st.markdown("## 🌟 Machine Readings", unsafe_allow_html=True)
cols = st.columns(len(MACHINES))

for i, machine in enumerate(MACHINES):
    data = st.session_state['LATEST_READINGS'][machine]
    risk = data.get("risk_level", "normal")
    color_map = {
        "normal": "linear-gradient(135deg,#096B6B , #008080)",
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
                          paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
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
