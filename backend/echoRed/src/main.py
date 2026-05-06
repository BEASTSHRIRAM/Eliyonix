"""
VidyutSeva - Rural Grid Modernization Agent System
Multi-agent system for detecting faults, forecasting load, and dispatching alerts
"""
import os
import json
import logging
from bedrock_agentcore import BedrockAgentCoreApp
from .orchestrator import get_orchestrator, reset_orchestrator
from .grid_state import SensorData

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock AgentCore
app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload: dict) -> dict:
    """
    Main entrypoint for VidyutSeva
    
    Payload format:
    {
        "sensor_data": {
            "voltage": 415.0,
            "current": 8.5,
            "temperature": 35.0,
            "timestamp": 1234567890.0,
            "inverter_id": "INV_001",
            "village_id": "KA_001"
        }
    }
    
    Returns:
    {
        "should_alert": bool,
        "alert_message": str,
        "fault_detected": bool,
        "anomaly_score": float,
        "fault_type": str,
        "demand_forecast": dict,
        "execution_id": str
    }
    """
    try:
        # Parse sensor data from payload
        sensor_input = payload.get("sensor_data", {})
        
        sensor_data: SensorData = {
            "voltage": sensor_input.get("voltage", 415.0),
            "current": sensor_input.get("current", 8.0),
            "temperature": sensor_input.get("temperature", 32.0),
            "timestamp": sensor_input.get("timestamp", 0),
            "inverter_id": sensor_input.get("inverter_id", "INV_UNKNOWN"),
            "village_id": sensor_input.get("village_id", "UNKNOWN"),
        }
        
        logger.info(f"Processing sensor data for {sensor_data['village_id']}")
        
        # Get orchestrator and process data
        orchestrator = get_orchestrator()
        result = await orchestrator.process_sensor_data(sensor_data)
        
        # Format response
        response = {
            "execution_id": result["execution_id"],
            "should_alert": result.get("should_alert", False),
            "alert_message": result.get("alert_message", ""),
            "fault_detected": result["fault_detected"],
            "anomaly_score": float(result["anomaly_score"]),
            "fault_type": result.get("fault_type", "unknown"),
            "is_demand_spike": result["is_demand_spike"],
            "demand_forecast": result.get("demand_forecast"),
            "errors": result.get("errors", []),
        }
        
        logger.info(f"Alert decision: {response['should_alert']}")
        return response
        
    except Exception as e:
        logger.error(f"Error in invoke: {e}", exc_info=True)
        return {
            "error": str(e),
            "should_alert": False,
            "alert_message": "",
            "fault_detected": False,
        }


@app.entrypoint
async def health_check(payload: dict) -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VidyutSeva",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    app.run()
