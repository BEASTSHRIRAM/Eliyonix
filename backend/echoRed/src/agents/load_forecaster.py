"""
Load Forecaster Agent
Predicts demand 2-4 hours ahead using LSTM-like logic
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

from ..grid_state import GridState, ForecastData
from ..a2a_protocol import get_message_broker, create_response_message
from ..memory_store import (
    get_memory_store,
    initialize_agent_memory,
    append_to_memory_list,
    get_load_forecaster_initial_memory,
)

logger = logging.getLogger(__name__)


class LoadForecaster:
    """Forecasts demand and helps disambiguate faults from demand spikes"""
    
    AGENT_NAME = "load_forecaster"
    
    def __init__(self):
        self.memory: Dict[str, Any] = {}
        # Simplified LSTM-like predictions (in production: use TensorFlow/PyTorch)
        self.hourly_patterns = {
            8: 0.9,    # Morning peak
            14: 1.0,   # Afternoon peak
            19: 0.95,  # Evening peak
            2: 0.3,    # Night low
        }
    
    async def initialize(self):
        """Initialize agent memory"""
        initial_memory = get_load_forecaster_initial_memory()
        self.memory = await initialize_agent_memory(self.AGENT_NAME, initial_memory)
        logger.info(f"Initialized {self.AGENT_NAME}")
    
    async def execute(self, state: GridState) -> GridState:
        """Execute load forecasting"""
        try:
            # Receive messages from Fault Detector
            broker = get_message_broker()
            messages = await broker.receive_messages(self.AGENT_NAME)
            
            # Process Fault Detector query if available
            fd_message = None
            for msg in messages:
                if msg["from_agent"] == "fault_detector" and msg["message_type"] == "query":
                    fd_message = msg
                    break
            
            # Forecast demand
            sensor_data = state["sensor_data"]
            forecast = await self._forecast_demand(sensor_data)
            
            # Determine if this is a demand spike
            current_demand = sensor_data.get("current", 0)  # Approximate demand
            demand_2h = forecast["demand_2h"]
            is_demand_spike = demand_2h > current_demand * 1.2
            
            logger.info(
                f"Load Forecast: current={current_demand:.1f}A, "
                f"2h_forecast={demand_2h:.1f}A, is_spike={is_demand_spike}"
            )
            
            # Send A2A response to Fault Detector
            if fd_message:
                await self._send_a2a_response(fd_message, forecast, is_demand_spike)
            
            # Update memory
            await append_to_memory_list(
                self.AGENT_NAME,
                "forecast_history",
                {
                    "timestamp": sensor_data["timestamp"],
                    "forecast": forecast,
                    "is_demand_spike": is_demand_spike,
                }
            )
            
            # Update state
            state["demand_forecast"] = forecast
            state["is_demand_spike"] = is_demand_spike
            state["load_forecaster_memory"] = self.memory
            
            return state
            
        except Exception as e:
            logger.error(f"Error in load forecasting: {e}")
            state["errors"].append(f"Load forecaster error: {str(e)}")
            return state
    
    async def _forecast_demand(self, sensor_data: Dict[str, Any]) -> ForecastData:
        """Forecast demand for next 2-4 hours"""
        current_hour = datetime.fromtimestamp(sensor_data["timestamp"]).hour
        current_demand = sensor_data.get("current", 0)  # Approximate
        
        # Simplified forecast based on hourly patterns
        hour_2h = (current_hour + 2) % 24
        hour_4h = (current_hour + 4) % 24
        
        baseline = 8.0  # Average demand
        demand_2h = baseline * self.hourly_patterns.get(hour_2h, 0.7)
        demand_4h = baseline * self.hourly_patterns.get(hour_4h, 0.7)
        
        # Add random variation
        demand_2h += np.random.normal(0, 0.3)
        demand_4h += np.random.normal(0, 0.3)
        
        return {
            "demand_current": current_demand,
            "demand_2h": max(0, demand_2h),
            "demand_4h": max(0, demand_4h),
            "is_demand_spike": False,
            "confidence": 0.85,
            "timestamp": sensor_data["timestamp"],
        }
    
    async def _send_a2a_response(self, fd_message: Dict, forecast: ForecastData, is_demand_spike: bool):
        """Send A2A response to Fault Detector"""
        broker = get_message_broker()
        
        response = create_response_message(
            from_agent=self.AGENT_NAME,
            to_agent="fault_detector",
            in_reply_to=fd_message["message_id"],
            payload={
                "forecast": forecast,
                "is_demand_spike": is_demand_spike,
                "confidence": forecast["confidence"],
                "reasoning": (
                    f"Forecasted demand at 2h: {forecast['demand_2h']:.1f}A. "
                    f"Current: {forecast['demand_current']:.1f}A. "
                    f"{'Likely demand spike.' if is_demand_spike else 'Likely NOT a demand spike.'}"
                ),
            }
        )
        
        await broker.send_message(response)
        logger.info(f"Sent A2A response to fault_detector: {response['message_id']}")


async def load_forecaster_node(state: GridState) -> GridState:
    """LangGraph node for Load Forecaster"""
    forecaster = LoadForecaster()
    await forecaster.initialize()
    return await forecaster.execute(state)
