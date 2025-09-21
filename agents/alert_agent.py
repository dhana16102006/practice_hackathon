from datetime import datetime

def create_alert(machine_id, payload, risk_result):
    return {
        "machine_id": machine_id,
        "message": f"CRITICAL ALERT: {machine_id} exceeded thresholds!",
        "timestamp": datetime.utcnow().isoformat(),
        "details": payload
    }
