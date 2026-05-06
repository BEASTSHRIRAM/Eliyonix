"""
VidyutSeva - Rural Grid Modernization Agent System
Multi-agent system for detecting faults, forecasting load, and dispatching alerts
"""
import os
import json
import logging
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from bedrock_agentcore import BedrockAgentCoreApp
from .orchestrator import get_orchestrator, reset_orchestrator
from .grid_state import SensorData

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock AgentCore
app = BedrockAgentCoreApp()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _invoke_agent(payload: dict) -> dict:
    """
    Core agent invocation logic
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
    return await _invoke_agent(payload)


@app.entrypoint
async def health_check(payload: dict) -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VidyutSeva",
        "version": "0.1.0",
    }


# FastAPI HTTP routes for frontend integration
async def http_health(request):
    """HTTP health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "VidyutSeva",
        "version": "0.1.0",
    })


async def agent_status(request):
    """Get current agent status"""
    try:
        orchestrator = get_orchestrator()
        return JSONResponse({
            "status": "running",
            "agents": {
                "fault_detector": "active",
                "load_forecaster": "active",
                "alert_dispatcher": "active",
            },
            "last_execution": None,
            "uptime": "running",
        })
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
        })


async def solar_selection(request):
    """Handle solar brand selection from mobile app"""
    try:
        data = await request.json()
        brand = data.get("brand")
        farmer_id = data.get("farmerId", "farmer_001")
        
        logger.info(f"Solar brand selection: {brand} from {farmer_id}")
        
        return JSONResponse({
            "status": "success",
            "message": f"Selected {brand} for farmer {farmer_id}",
            "brand": brand,
            "farmerId": farmer_id,
        })
    except Exception as e:
        logger.error(f"Error processing solar selection: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
        })


async def http_invoke(request):
    """HTTP endpoint for invoking the agent"""
    try:
        payload = await request.json()
        result = await _invoke_agent(payload)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in http_invoke: {e}", exc_info=True)
        return JSONResponse({
            "error": str(e),
            "should_alert": False,
            "alert_message": "",
            "fault_detected": False,
        }, status_code=500)

# Add routes
app.add_route("/health", http_health, methods=["GET"])
app.add_route("/agent/status", agent_status, methods=["GET"])
app.add_route("/invoke", http_invoke, methods=["POST"])
app.add_route("/solar-selection", solar_selection, methods=["POST"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
