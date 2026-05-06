"""
MQTT PubSub subscriber for live inverter sensor readings.

Run this beside the API server. It subscribes to sensor topics and publishes
each message into the same agent pipeline used by the dashboard live state.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

import paho.mqtt.client as mqtt

from .main import _invoke_agent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensor/data")


def _normalise_sensor_payload(topic: str, payload: dict) -> dict:
    parts = topic.split("/")
    village_id = payload.get("village_id") or (parts[1].upper() if len(parts) > 1 else "KA_001")
    inverter_id = payload.get("inverter_id") or (parts[3].upper() if len(parts) > 3 else "INV_001")

    return {
        "voltage": float(payload.get("voltage", payload.get("v", 0))),
        "current": float(payload.get("current", payload.get("i", 0))),
        "temperature": float(payload.get("temperature", payload.get("t", 0))),
        "humidity": float(payload.get("humidity", 0)),
        "ldr": payload.get("ldr"),
        "timestamp": float(payload.get("timestamp", datetime.now().timestamp())),
        "inverter_id": inverter_id,
        "village_id": village_id,
    }


async def _process_message(topic: str, raw_payload: bytes):
    try:
      payload = json.loads(raw_payload.decode("utf-8"))
      sensor_data = _normalise_sensor_payload(topic, payload)
      await _invoke_agent({"sensor_data": sensor_data})
      logger.info("Processed MQTT message from %s", topic)
    except Exception as exc:
      logger.exception("Failed to process MQTT message from %s: %s", topic, exc)


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties):
        logger.info("Connected to MQTT broker %s:%s with code %s", MQTT_HOST, MQTT_PORT, reason_code)
        client.subscribe(MQTT_TOPIC)
        logger.info("Subscribed to %s", MQTT_TOPIC)

    def on_message(client, userdata, message):
        asyncio.run_coroutine_threadsafe(_process_message(message.topic, message.payload), loop)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    try:
        loop.run_forever()
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
