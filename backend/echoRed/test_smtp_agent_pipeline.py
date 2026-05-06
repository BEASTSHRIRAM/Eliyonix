"""
Run the AlertDispatcher agent path and send a test SMTP alert.

This does not require the HTTP server. It loads .env, creates a high-confidence
fault state, and lets the 3rd agent execute the configured notification tool.
"""
import asyncio

from dotenv import load_dotenv

from src.agents.alert_dispatcher import AlertDispatcher
from src.grid_state import create_empty_grid_state
from src.memory_store import InMemoryStore, set_memory_store


async def main():
    load_dotenv(override=True)
    set_memory_store(InMemoryStore())

    dispatcher = AlertDispatcher()
    await dispatcher.initialize()

    state = create_empty_grid_state(
        {
            "voltage": 440.0,
            "current": 5.0,
            "temperature": 45.0,
            "timestamp": 1234567890,
            "inverter_id": "INV_002",
            "village_id": "KA_001",
        },
        "smtp-test",
    )
    state["fault_detected"] = True
    state["is_demand_spike"] = False
    state["anomaly_score"] = 1.0
    state["fault_type"] = "inverter_overvoltage"

    result = await dispatcher.execute(state)

    print("should_alert=", result.get("should_alert"))
    print("alert_message=", result.get("alert_message"))
    print("notification_status=", result.get("telegram_status"))


if __name__ == "__main__":
    asyncio.run(main())
