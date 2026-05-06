"""
Alert Dispatcher Agent
Decides whether to send alerts and generates localized messages via Bedrock
"""
from typing import Dict, Any, Optional
import logging

from ..grid_state import GridState
from ..a2a_protocol import get_message_broker
from ..memory_store import (
    get_memory_store,
    initialize_agent_memory,
    append_to_memory_list,
    get_alert_dispatcher_initial_memory,
)
from ..bedrock_integration import get_alert_generator

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
                
                # Log alert
                await append_to_memory_list(
                    self.AGENT_NAME,
                    "alerts_sent",
                    {
                        "timestamp": state["timestamp"],
                        "fault_type": state["fault_type"],
                        "message": alert_message,
                        "recipient": state["sensor_data"].get("village_id", "unknown"),
                        "status": "sent",
                        "confidence": state["anomaly_score"],
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
        alert_generator = get_alert_generator()
        
        sensor_data = state["sensor_data"]
        fault_type = state.get("fault_type", "inverter_fault")
        village_id = sensor_data.get("village_id", "unknown")
        inverter_id = sensor_data.get("inverter_id", "unknown")
        confidence = state["anomaly_score"]
        
        # Determine language (simplified: use Kannada for now)
        language = state.get("alert_language", "kannada")
        
        try:
            if language == "kannada":
                alert_message = await alert_generator.generate_alert_kannada(
                    fault_type=fault_type,
                    village_id=village_id,
                    confidence=confidence,
                    inverter_id=inverter_id,
                    sensor_data=sensor_data,
                )
            elif language == "hindi":
                alert_message = await alert_generator.generate_alert_hindi(
                    fault_type=fault_type,
                    village_id=village_id,
                    confidence=confidence,
                    inverter_id=inverter_id,
                    sensor_data=sensor_data,
                )
            else:
                alert_message = f"Alert: {fault_type.replace('_', ' ')} in {village_id}"
            
            logger.info(f"Generated alert in {language}: {alert_message}")
            return alert_message
            
        except Exception as e:
            logger.error(f"Error generating alert: {e}")
            return f"Alert: {fault_type} in {village_id}"


async def alert_dispatcher_node(state: GridState) -> GridState:
    """LangGraph node for Alert Dispatcher"""
    dispatcher = AlertDispatcher()
    await dispatcher.initialize()
    return await dispatcher.execute(state)
