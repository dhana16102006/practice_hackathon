import os
import requests

MISTRAL_API_KEY = os.getenv("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")  # put your key in environment variable
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"  # adjust if endpoint different

def classify_risk(reading):
    """
    Call Mistral API to classify risk level based on sensor reading.
    """
    if not MISTRAL_API_KEY:
        # fallback to simple threshold
        temp = reading.get("temperature", 0)
        vib = reading.get("vibration", 0)
        gas = reading.get("gas_level", 0)
        risk_level = "critical" if temp > 90 or vib > 4 or gas > 15 else "normal"
        return {"risk_level": risk_level}

    prompt = f"""
    Sensor reading: Temperature={reading['temperature']}, Vibration={reading['vibration']}, Gas={reading['gas_level']}.
    Classify risk as one of: normal, warning, critical. Return JSON like {{ "risk_level": "critical" }} only.
    """

    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
      "model": "mistral-small",  # pick available model
      "messages": [{"role": "user", "content": prompt}],
    }

    try:
        r = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=10)
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        import json
        risk_json = json.loads(content)
        return risk_json
    except Exception as e:
        print("Mistral error:", e)
        return {"risk_level": "normal"}
