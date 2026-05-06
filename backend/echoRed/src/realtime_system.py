"""
Minimal real-time IoT intelligence pipeline.

Data flow:
ESP32 -> MQTT broker topic "sensor/data" -> Python subscriber -> 3 agents
-> in-memory latest state -> REST /data and WebSocket /ws/data -> frontend.

This module intentionally keeps the transport and agent boundaries small so it
can run on a Windows laptop or Raspberry Pi during demos.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional, Set

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensor/data")


class SensorPayload(BaseModel):
    """Exact ESP32 JSON contract accepted from MQTT and debug HTTP POSTs."""

    temperature: float
    humidity: float = 0.0
    voltage: float
    current: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProcessedOutput(BaseModel):
    """Exact frontend contract requested for the dashboard."""

    status: str
    fault: str
    forecast: str
    action: str


class FaultDetectionAgent:
    """Detects obvious electrical/thermal faults from one sensor snapshot."""

    def run(self, sensor: SensorPayload) -> Dict[str, Any]:
        if sensor.temperature >= 70:
            return {
                "fault": "overheat",
                "severity": "critical",
                "confidence": 0.96,
                "reason": f"temperature {sensor.temperature:.1f}C exceeds 70C",
            }
        if sensor.temperature >= 55:
            return {
                "fault": "high_temperature",
                "severity": "warning",
                "confidence": 0.82,
                "reason": f"temperature {sensor.temperature:.1f}C exceeds 55C",
            }
        if sensor.voltage < 180:
            return {
                "fault": "undervoltage",
                "severity": "critical",
                "confidence": 0.9,
                "reason": f"voltage {sensor.voltage:.1f}V is below operating range",
            }
        if sensor.current > 15:
            return {
                "fault": "overcurrent",
                "severity": "critical",
                "confidence": 0.9,
                "reason": f"current {sensor.current:.1f}A exceeds safe range",
            }
        return {
            "fault": "none",
            "severity": "normal",
            "confidence": 0.88,
            "reason": "all readings within expected range",
        }


class LoadForecastingAgent:
    """Classifies near-term load direction from live power and heat stress."""

    def run(self, sensor: SensorPayload) -> Dict[str, Any]:
        power_kw = sensor.voltage * sensor.current / 1000
        if power_kw >= 4.5 or sensor.current >= 12:
            forecast = "increasing_load"
            confidence = 0.84
        elif power_kw <= 1.0:
            forecast = "low_generation"
            confidence = 0.78
        else:
            forecast = "stable_load"
            confidence = 0.8

        return {
            "forecast": forecast,
            "power_kw": round(power_kw, 2),
            "confidence": confidence,
        }


class AlertDispatchAgent:
    """Turns agent decisions into one clear operator/farmer action."""

    def run(self, fault_result: Dict[str, Any], forecast_result: Dict[str, Any]) -> Dict[str, Any]:
        fault = fault_result["fault"]
        forecast = forecast_result["forecast"]
        severity = fault_result["severity"]

        if severity == "critical":
            action = "reduce load immediately"
            status = "critical"
        elif severity == "warning" or forecast == "increasing_load":
            action = "inspect panel and monitor load"
            status = "warning"
        else:
            action = "no action required"
            status = "normal"

        return {
            "status": status,
            "action": action,
            "message": f"{fault}; {forecast}; {action}",
        }


@dataclass
class AgentPipeline:
    """Small orchestrator that runs the 3 agents in a fixed sequence."""

    fault_agent: FaultDetectionAgent
    forecast_agent: LoadForecastingAgent
    alert_agent: AlertDispatchAgent

    def process(self, sensor: SensorPayload) -> Dict[str, Any]:
        fault_result = self.fault_agent.run(sensor)
        forecast_result = self.forecast_agent.run(sensor)
        alert_result = self.alert_agent.run(fault_result, forecast_result)

        output = ProcessedOutput(
            status=alert_result["status"],
            fault=fault_result["fault"],
            forecast=forecast_result["forecast"],
            action=alert_result["action"],
        ).model_dump()

        return {
            **output,
            "sensor": sensor.model_dump(),
            "agents": {
                "fault_detection": fault_result,
                "load_forecasting": forecast_result,
                "alert_dispatch": alert_result,
            },
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }


class LatestStateStore:
    """Thread-safe memory store read by REST and WebSocket clients."""

    def __init__(self):
        self._lock = Lock()
        self._latest: Dict[str, Any] = {
            "status": "waiting",
            "fault": "none",
            "forecast": "waiting_for_sensor_data",
            "action": "connect ESP32 MQTT publisher",
        }

    def set(self, value: Dict[str, Any]) -> None:
        with self._lock:
            self._latest = value

    def get(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._latest)


class WebSocketHub:
    """Tracks dashboard WebSocket connections and broadcasts processed updates."""

    def __init__(self):
        self._clients: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        disconnected = []
        for websocket in self._clients:
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(websocket)


pipeline = AgentPipeline(
    fault_agent=FaultDetectionAgent(),
    forecast_agent=LoadForecastingAgent(),
    alert_agent=AlertDispatchAgent(),
)
state_store = LatestStateStore()
ws_hub = WebSocketHub()

app = FastAPI(title="Eliyonix Real-Time IoT Pipeline")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_mqtt_client: Optional[mqtt.Client] = None


async def process_sensor_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ESP32 data, run agents, store state, and notify dashboards."""
    sensor = SensorPayload(**payload)
    processed = pipeline.process(sensor)
    state_store.set(processed)
    await ws_hub.broadcast(processed)
    logger.info("Processed sensor payload: status=%s fault=%s", processed["status"], processed["fault"])
    return processed


def _start_mqtt_subscriber(event_loop: asyncio.AbstractEventLoop) -> mqtt.Client:
    """Start continuous MQTT listening in paho's network thread."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties):
        logger.info("Connected to MQTT broker %s:%s; subscribing to %s", MQTT_HOST, MQTT_PORT, MQTT_TOPIC)
        client.subscribe(MQTT_TOPIC)

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            logger.exception("Invalid JSON on MQTT topic %s", message.topic)
            return

        # paho callbacks run outside the asyncio loop, so hand work back to FastAPI's loop.
        event_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(process_sensor_payload(payload))
        )

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


@app.on_event("startup")
async def startup_event() -> None:
    """Boot MQTT subscriber when the API starts."""
    global _mqtt_client
    loop = asyncio.get_running_loop()
    try:
        _mqtt_client = _start_mqtt_subscriber(loop)
    except Exception as exc:
        logger.error("MQTT subscriber could not start: %s", exc)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanly stop MQTT networking on app shutdown."""
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy", "mqtt_topic": MQTT_TOPIC}


@app.get("/data")
async def get_data() -> Dict[str, Any]:
    """Frontend polls this endpoint every 2-3 seconds for latest processed result."""
    return state_store.get()


@app.get("/grid/live")
async def get_grid_live() -> Dict[str, Any]:
    """
    Compatibility endpoint for the existing Eliyonix frontend.

    New minimal dashboards can read /data directly. The current frontend still
    polls /grid/live, so this wraps the same latest processed state in the
    shape those dashboard components expect.
    """
    latest = state_store.get()
    sensor = latest.get("sensor", {})
    power_kw = None
    if sensor.get("voltage") is not None and sensor.get("current") is not None:
        power_kw = round(float(sensor["voltage"]) * float(sensor["current"]) / 1000, 2)

    agent_result = {
        "fault_detected": latest.get("fault") not in (None, "none"),
        "fault_type": latest.get("fault", "none"),
        "anomaly_score": 1.0 if latest.get("status") == "critical" else 0.5 if latest.get("status") == "warning" else 0.0,
        "should_alert": latest.get("status") in ("warning", "critical"),
        "alert_message": latest.get("action", ""),
        "is_demand_spike": latest.get("forecast") == "increasing_load",
        "demand_forecast": {
            "demand_current": sensor.get("current"),
            "demand_2h": power_kw,
            "confidence": latest.get("agents", {}).get("load_forecasting", {}).get("confidence", 0),
        },
    }

    record = {
        "source": "mqtt",
        "topic": MQTT_TOPIC,
        "sensor_data": {
            **sensor,
            "village_id": "KA_001",
            "inverter_id": "INV_001",
            "power_kw": power_kw,
        },
        "agent_result": agent_result,
        "derived": {
            "power_kw": power_kw,
            "panel_health": max(0, 100 - round(agent_result["anomaly_score"] * 100)),
            "status": latest.get("status", "waiting").upper(),
        },
        "updated_at": latest.get("processed_at"),
    }

    return {
        "status": "connected" if latest.get("processed_at") else "waiting_for_mqtt",
        "latest": record if latest.get("processed_at") else None,
        "logs": [record["sensor_data"]] if latest.get("processed_at") else [],
        "alerts": [{
            "severity": latest.get("status"),
            "message": latest.get("action"),
            "timestamp": latest.get("processed_at"),
            "village_id": "KA_001",
        }] if latest.get("status") in ("warning", "critical") else [],
        "sites": [record] if latest.get("processed_at") else [],
    }


@app.post("/data")
async def post_data(payload: SensorPayload) -> Dict[str, Any]:
    """Debug endpoint: submit the same JSON that ESP32 publishes to MQTT."""
    return await process_sensor_payload(payload.model_dump())


@app.websocket("/ws/data")
async def websocket_data(websocket: WebSocket) -> None:
    """Optional real-time push endpoint for dashboards."""
    await ws_hub.connect(websocket)
    await websocket.send_json(state_store.get())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
