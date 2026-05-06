"""
In-memory live grid state for MQTT-style PubSub ingestion.

The MQTT subscriber writes every published sensor payload here after the
agent pipeline processes it. Dashboards read this state instead of generating
their own sample data.
"""
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional


MAX_SENSOR_LOGS = 50
MAX_ALERTS = 20

_latest_by_village: Dict[str, Dict[str, Any]] = {}
_sensor_logs: deque[Dict[str, Any]] = deque(maxlen=MAX_SENSOR_LOGS)
_alerts: deque[Dict[str, Any]] = deque(maxlen=MAX_ALERTS)


def update_live_state(sensor_data: Dict[str, Any], agent_result: Dict[str, Any]) -> Dict[str, Any]:
    village_id = sensor_data.get("village_id", "UNKNOWN")
    timestamp = sensor_data.get("timestamp") or datetime.now().timestamp()
    voltage = float(sensor_data.get("voltage", 0) or 0)
    current = float(sensor_data.get("current", 0) or 0)
    temperature = float(sensor_data.get("temperature", 0) or 0)
    ldr = sensor_data.get("ldr")
    power_kw = round((voltage * current) / 1000, 2)
    anomaly_score = float(agent_result.get("anomaly_score", 0) or 0)
    fault_detected = bool(agent_result.get("fault_detected", False))
    should_alert = bool(agent_result.get("should_alert", False))
    alert_message = agent_result.get("alert_message") or ""

    record = {
        "source": "mqtt",
        "topic": f"village/{village_id.lower()}/sensors/{sensor_data.get('inverter_id', 'unknown').lower()}",
        "sensor_data": {
            **sensor_data,
            "timestamp": timestamp,
            "power_kw": power_kw,
        },
        "agent_result": agent_result,
        "derived": {
            "power_kw": power_kw,
            "panel_health": max(0, min(100, round(100 - (anomaly_score * 100)))),
            "status": "FAULT" if fault_detected else "HEALTHY",
            "active_alerts": 1 if should_alert else 0,
        },
        "updated_at": datetime.fromtimestamp(float(timestamp)).isoformat(),
    }

    _latest_by_village[village_id] = record
    _sensor_logs.appendleft({
        "timestamp": timestamp,
        "village_id": village_id,
        "inverter_id": sensor_data.get("inverter_id", "UNKNOWN"),
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "ldr": ldr,
        "power_kw": power_kw,
    })

    if should_alert or fault_detected:
        _alerts.appendleft({
            "timestamp": timestamp,
            "village_id": village_id,
            "severity": "critical" if should_alert else "warning",
            "message": alert_message or agent_result.get("fault_type", "Fault detected"),
        })

    return record


def get_live_state(village_id: Optional[str] = None) -> Dict[str, Any]:
    if village_id:
        latest = _latest_by_village.get(village_id)
    else:
        latest = next(iter(_latest_by_village.values()), None)

    return {
        "status": "connected" if latest else "waiting_for_mqtt",
        "latest": latest,
        "logs": list(_sensor_logs),
        "alerts": list(_alerts),
        "sites": list(_latest_by_village.values()),
    }
