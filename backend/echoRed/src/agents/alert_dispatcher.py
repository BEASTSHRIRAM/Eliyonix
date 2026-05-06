"""
Alert Dispatcher Agent
Decides whether to send alerts and generates localized messages via Bedrock
"""
from typing import Dict, Any, Optional
import logging
import os

from ..grid_state import GridState
from ..a2a_protocol import get_message_broker
from ..memory_store import (
    get_memory_store,
    initialize_agent_memory,
    append_to_memory_list,
    get_alert_dispatcher_initial_memory,
)
from ..bedrock_integration import get_alert_generator
from ..smtp_mcp_tool import build_smtp_tool_args, execute_smtp_notify_tool
from ..telegram_mcp_tool import build_telegram_tool_args, execute_telegram_notify_tool

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Decides when to send alerts and generates localized messages"""
    
    AGENT_NAME = "alert_dispatcher"
    ALERT_CONFIDENCE_THRESHOLD = 0.75
    
    def __init__(self):
        self.memory: Dict[str, Any] = {}
    
    async def initialize(self):
        """Initialize agent memory"""
        initial_memory = get_alert_dispatcher_initial_memory()
        self.memory = await initialize_agent_memory(self.AGENT_NAME, initial_memory)
        logger.info(f"Initialized {self.AGENT_NAME}")
    
    async def execute(self, state: GridState) -> GridState:
        """Execute alert decision logic and generation"""
        try:
            # Consensus logic
            should_alert = self._should_alert(state)
            
            logger.info(
                f"Alert Decision: should_alert={should_alert} "
                f"(fault={state['fault_detected']}, "
                f"demand_spike={state['is_demand_spike']}, "
                f"confidence={state['anomaly_score']:.2f})"
            )
            
            if should_alert:
                # Generate alert message
                alert_message = await self._generate_alert(state)
                state["alert_message"] = alert_message
                state["should_alert"] = True
                state["telegram_status"] = await self._send_alert_tool(state, alert_message)
                
                # Log alert
                await append_to_memory_list(
                    self.AGENT_NAME,
                    "alerts_sent",
                    {
                        "timestamp": state["timestamp"],
                        "fault_type": state["fault_type"],
                        "message": alert_message,
                        "recipient": state["sensor_data"].get("village_id", "unknown"),
                        "status": state["telegram_status"].get("status", "generated"),
                        "confidence": state["anomaly_score"],
                        "telegram": state["telegram_status"],
                    }
                )
            else:
                # Log non-alert decision
                reason = (
                    "demand_spike" if state["is_demand_spike"]
                    else "low_confidence"
                )
                await append_to_memory_list(
                    self.AGENT_NAME,
                    "non_alerts",
                    {
                        "timestamp": state["timestamp"],
                        "reason": reason,
                        "fault_type": state["fault_type"],
                        "confidence": state["anomaly_score"],
                    }
                )
                state["should_alert"] = False
                state["telegram_status"] = {
                    "enabled": False,
                    "sent": False,
                    "status": "not_required",
                    "chat_id": None,
                    "error": None,
                }
            
            state["alert_dispatcher_memory"] = self.memory
            return state
            
        except Exception as e:
            logger.error(f"Error in alert dispatch: {e}")
            state["errors"].append(f"Alert dispatcher error: {str(e)}")
            state["should_alert"] = False
            return state
    
    def _should_alert(self, state: GridState) -> bool:
        """
        Consensus logic: decide if alert should be sent
        
        Rule: Alert if (fault detected AND NOT demand spike AND high confidence)
        """
        should_alert = (
            state["fault_detected"] and
            not state["is_demand_spike"] and
            state["anomaly_score"] > self.ALERT_CONFIDENCE_THRESHOLD
        )
        
        return should_alert
    
    async def _generate_alert(self, state: GridState) -> str:
        """Generate alert message in appropriate language"""
        sensor_data = state["sensor_data"]
        fault_type = state.get("fault_type", "inverter_fault")
        village_id = sensor_data.get("village_id", "unknown")
        inverter_id = sensor_data.get("inverter_id", "unknown")
        confidence = state["anomaly_score"]
        
        # Generate clear English alert message
        fault_descriptions = {
            "inverter_overvoltage": "Overvoltage detected",
            "inverter_undervoltage": "Undervoltage detected",
            "inverter_overtemp": "Overheating detected",
            "inverter_undertemp": "Low temperature detected",
            "inverter_overcurrent": "Overcurrent detected",
            "inverter_fault": "Fault detected",
        }
        
        fault_desc = fault_descriptions.get(fault_type, fault_type.replace("_", " ").title())
        
        # Format alert message
        alert_message = f"ALERT: {fault_desc} in {village_id} (Inverter: {inverter_id}). Confidence: {confidence*100:.0f}%. Voltage: {sensor_data.get('voltage', 0):.1f}V, Current: {sensor_data.get('current', 0):.1f}A, Temp: {sensor_data.get('temperature', 0):.1f}°C"
        
        logger.info(f"Generated alert: {alert_message}")
        return alert_message

    async def _send_alert_tool(self, state: GridState, alert_message: str) -> Dict[str, Any]:
        """Reason about delivery and execute the configured notification MCP tool."""
        if not self._should_use_telegram_tool(state):
            return {
                "enabled": False,
                "sent": False,
                "status": "tool_not_required",
                "chat_id": None,
                "error": None,
            }

        preferred_channel = os.getenv("ALERT_CHANNEL", "telegram").lower()
        if preferred_channel == "smtp":
            return await self._send_smtp_alert(state, alert_message)

        return await self._send_telegram_alert(state, alert_message)

    async def _send_smtp_alert(self, state: GridState, alert_message: str) -> Dict[str, Any]:
        """Execute the SMTP MCP notification tool."""
        sensor_data = state["sensor_data"]
        tool_args = build_smtp_tool_args(
            sensor_data=sensor_data,
            alert_message=alert_message,
            fault_type=state.get("fault_type"),
            confidence=state["anomaly_score"],
        )
        logger.info("Alert dispatcher chose MCP tool '%s'", tool_args["tool_name"])
        return await execute_smtp_notify_tool(tool_args)

    async def _send_telegram_alert(self, state: GridState, alert_message: str) -> Dict[str, Any]:
        """Execute the Telegram MCP notification tool."""
        sensor_data = state["sensor_data"]
        tool_args = build_telegram_tool_args(
            sensor_data=sensor_data,
            alert_message=alert_message,
            fault_type=state.get("fault_type"),
            confidence=state["anomaly_score"],
        )
        logger.info(
            "Alert dispatcher chose MCP tool '%s' for fault_type=%s confidence=%.2f",
            tool_args.get("tool_name", "telegram_notify_farmer"),
            state.get("fault_type"),
            state["anomaly_score"],
        )
        result = await execute_telegram_notify_tool(tool_args)

        if result.get("sent"):
            logger.info("Telegram MCP tool sent alert to chat_id=%s", result.get("chat_id"))
        else:
            logger.warning("Telegram MCP tool did not send alert: %s", result.get("error") or result.get("status"))

        return result

    def _should_use_telegram_tool(self, state: GridState) -> bool:
        """
        Tool-use reasoning for the third agent.

        The agent only executes the Telegram MCP tool after consensus says this is
        a real high-confidence fault, not a demand spike.
        """
        return (
            state["fault_detected"]
            and not state["is_demand_spike"]
            and state["anomaly_score"] > self.ALERT_CONFIDENCE_THRESHOLD
        )


async def alert_dispatcher_node(state: GridState) -> GridState:
    """LangGraph node for Alert Dispatcher"""
    dispatcher = AlertDispatcher()
    await dispatcher.initialize()
    return await dispatcher.execute(state)
