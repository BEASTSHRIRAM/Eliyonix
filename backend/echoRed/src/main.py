"""
VidyutSeva - Rural Grid Modernization Agent System
Multi-agent system for detecting faults, forecasting load, and dispatching alerts
"""
import os
import json
import logging
from dotenv import load_dotenv
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from bedrock_agentcore import BedrockAgentCoreApp
from .orchestrator import get_orchestrator, reset_orchestrator
from .grid_state import SensorData
from .vector_store import get_vector_store
from .recommendation_scheduler import get_scheduler, create_scheduler
from .agents.recommendation_agent import RecommendationAgent
from .recommendation_engine import get_recommendation_engine
from .live_state import get_live_state, update_live_state
from .voice_agent import handle_voice_agent_request

load_dotenv(override=True)

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
            "telegram_status": result.get("telegram_status"),
            "fault_detected": result["fault_detected"],
            "anomaly_score": float(result["anomaly_score"]),
            "fault_type": result.get("fault_type", "unknown"),
            "is_demand_spike": result["is_demand_spike"],
            "demand_forecast": result.get("demand_forecast"),
            "recommendations": result.get("recommendations", {}),
            "errors": result.get("errors", []),
        }
        update_live_state(sensor_data, response)
        
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


async def mqtt_publish(request):
    """HTTP bridge for MQTT subscribers to publish sensor messages into the agent pipeline."""
    try:
        payload = await request.json()
        sensor_data = payload.get("sensor_data", payload)
        result = await _invoke_agent({"sensor_data": sensor_data})
        return JSONResponse({
            "status": "published",
            "topic": payload.get("topic"),
            "result": result,
        })
    except Exception as e:
        logger.error(f"Error processing MQTT publish: {e}", exc_info=True)
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


async def live_grid_state(request):
    """Read latest MQTT-fed grid state for dashboards."""
    village_id = request.query_params.get("village_id")
    return JSONResponse(get_live_state(village_id))


# Recommendation endpoints
async def get_recommendations(request):
    """Get latest recommendations for all components"""
    try:
        vector_store = get_vector_store()
        scheduler = get_scheduler()
        
        # Get the last 1 recommendation per component
        stats = vector_store.get_stats()
        recommendations = {}
        
        for component in ["solar", "fault", "forecast", "alerts", "sensor", "agents"]:
            # Find the most recent document for this component
            docs = [d for d in vector_store.documents if d.get('component') == component]
            if docs:
                latest = max(docs, key=lambda x: x.get('timestamp', ''))
                recommendations[component] = {
                    'text': latest.get('recommendation_text', ''),
                    'confidence': latest.get('confidence', 0),
                    'status': latest.get('status', 'MONITOR'),
                    'timestamp': latest.get('timestamp', ''),
                }
        
        scheduler_status = scheduler.get_status() if scheduler else {
            'is_running': False,
            'time_until_next_minutes': None
        }
        
        return JSONResponse({
            'recommendations': recommendations,
            'vector_store_stats': stats,
            'scheduler_status': scheduler_status,
        })
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return JSONResponse({
            'error': str(e),
            'recommendations': {}
        }, status_code=500)


async def get_recommendation_history(request):
    """Get recommendation history (last 24 hours by default)"""
    try:
        vector_store = get_vector_store()
        component = request.query_params.get('component', None)
        limit = int(request.query_params.get('limit', 50))
        
        # Filter documents
        docs = vector_store.documents
        if component:
            docs = [d for d in docs if d.get('component') == component]
        
        # Sort by timestamp descending and limit
        docs = sorted(docs, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
        
        # Format response
        history = []
        for doc in docs:
            history.append({
                'timestamp': doc.get('timestamp', ''),
                'component': doc.get('component', ''),
                'text': doc.get('recommendation_text', ''),
                'confidence': doc.get('confidence', 0),
                'status': doc.get('status', 'MONITOR'),
                'similarity_score': doc.get('similarity_score', 0),
                'retrieved_events': [
                    {
                        'timestamp': e.get('timestamp', ''),
                        'text': e.get('recommendation_text', ''),
                    }
                    for e in docs  # In production, retrieve from vector store
                ][:3],
            })
        
        return JSONResponse({
            'history': history,
            'total_count': len(history),
            'component_filter': component,
        })
    except Exception as e:
        logger.error(f"Error getting recommendation history: {e}")
        return JSONResponse({
            'error': str(e),
            'history': []
        }, status_code=500)


async def trigger_recommendations(request):
    """Manually trigger recommendation generation"""
    try:
        scheduler = get_scheduler()
        if scheduler:
            scheduler.trigger_now()
            return JSONResponse({
                'status': 'triggered',
                'message': 'Recommendation generation triggered'
            })
        else:
            return JSONResponse({
                'status': 'error',
                'message': 'Recommendation scheduler not initialized'
            }, status_code=500)
    except Exception as e:
        logger.error(f"Error triggering recommendations: {e}")
        return JSONResponse({
            'error': str(e)
        }, status_code=500)


async def get_vector_store_status(request):
    """Get vector store statistics and status"""
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"Error getting vector store status: {e}")
        return JSONResponse({
            'error': str(e)
        }, status_code=500)


async def scheduler_status_endpoint(request):
    """Get recommendation scheduler status"""
    try:
        scheduler = get_scheduler()
        if scheduler:
            return JSONResponse(scheduler.get_status())
        else:
            return JSONResponse({
                'status': 'not_initialized',
                'message': 'Scheduler not initialized'
            })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return JSONResponse({
            'error': str(e)
        }, status_code=500)


async def get_component_recommendation(request):
    """Get recommendation for a specific component only"""
    try:
        component = request.path_params.get('component', '').lower()
        
        # Validate component
        valid_components = ["solar", "fault", "forecast", "alerts", "sensor", "agents"]
        if component not in valid_components:
            return JSONResponse({
                'error': f'Invalid component. Must be one of: {", ".join(valid_components)}',
                'recommendation': None
            }, status_code=400)
        
        logger.info(f"Fetching recommendation for component: {component}")
        
        # Get recommendation agent
        recommendation_agent = RecommendationAgent()
        
        # Retrieve similar events from vector store for this component only
        vector_store = get_vector_store()
        similar_events = vector_store.retrieve_similar(component, top_k=3)
        
        # Create minimal state with only this component's data
        from .grid_state import create_empty_grid_state
        state = create_empty_grid_state()
        state['grid_state'] = {
            'current_metrics': {
                'voltage': 415.0,
                'current': 8.0,
                'frequency': 50.0,
                'temperature': 32.0
            }
        }
        
        # Generate recommendation for this component only
        recommendation_data = recommendation_agent._generate_recommendation(component, state)
        
        # Format response
        return JSONResponse({
            'component': component,
            'recommendation': {
                'text': recommendation_data.get('text', ''),
                'confidence': recommendation_data.get('confidence', 0),
                'status': recommendation_data.get('status', 'MONITOR'),
                'timestamp': recommendation_data.get('timestamp', ''),
                'retrieved_events_count': len(similar_events),
                'retrieved_events': [
                    {
                        'timestamp': e.get('timestamp', ''),
                        'text': e.get('recommendation_text', ''),
                        'component': e.get('component', '')
                    } for e in similar_events
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting component recommendation: {e}", exc_info=True)
        return JSONResponse({
            'error': str(e),
            'recommendation': None
        }, status_code=500)


async def get_ai_recommendations(request):
    """
    Get AI recommendations based on 7-day historical patterns from Qdrant
    Uses semantic search to analyze patterns and provide intelligent suggestions
    """
    try:
        # Get village_id from query params (default to KA_001)
        village_id = request.query_params.get('village_id', 'KA_001')
        
        # Get current sensor data if provided
        current_sensor_data = None
        if request.method == 'POST':
            body = await request.json()
            current_sensor_data = body.get('current_sensor_data')
        
        logger.info(f"Generating AI recommendations for village: {village_id}")
        
        # Get recommendation engine and generate recommendations
        engine = get_recommendation_engine()
        result = await engine.get_recommendations(village_id, current_sensor_data)
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}", exc_info=True)
        return JSONResponse({
            'status': 'error',
            'message': str(e),
            'recommendations': []
        }, status_code=500)


async def voice_agent_handler(request):
    """Handle voice agent requests with LLM, weather, and recommendations"""
    try:
        body = await request.json()
        result = await handle_voice_agent_request(body)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in voice agent handler: {e}", exc_info=True)
        return JSONResponse({
            'error': str(e),
            'response': 'Sorry, I encountered an error. Please try again.'
        }, status_code=500)

app.add_route("/health", http_health, methods=["GET"])
app.add_route("/agent/status", agent_status, methods=["GET"])
app.add_route("/invoke", http_invoke, methods=["POST"])
app.add_route("/mqtt/publish", mqtt_publish, methods=["POST"])
app.add_route("/grid/live", live_grid_state, methods=["GET"])
app.add_route("/solar-selection", solar_selection, methods=["POST"])
app.add_route("/recommendations", get_recommendations, methods=["GET"])
app.add_route("/recommendations/ai", get_ai_recommendations, methods=["GET", "POST"])
app.add_route("/recommendations/{component}", get_component_recommendation, methods=["GET"])
app.add_route("/recommendations/history", get_recommendation_history, methods=["GET"])
app.add_route("/recommendations/trigger", trigger_recommendations, methods=["POST"])
app.add_route("/vector-store/status", get_vector_store_status, methods=["GET"])
app.add_route("/scheduler/status", scheduler_status_endpoint, methods=["GET"])
app.add_route("/api/voice-agent", voice_agent_handler, methods=["POST"])


# Recommendation generation callback for scheduler
async def scheduled_recommendation_callback():
    """Callback function for the recommendation scheduler"""
    try:
        logger.info("Running scheduled recommendation generation")
        
        # Generate a synthetic sensor reading to trigger recommendations
        orchestrator = get_orchestrator()
        sensor_data: SensorData = {
            "voltage": 415.0,
            "current": 8.0,
            "temperature": 32.0,
            "timestamp": 0,  # Will be set by agent
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        logger.info(f"Scheduled recommendation generation completed")
        
    except Exception as e:
        logger.error(f"Error in scheduled recommendation callback: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Initialize and start the recommendation scheduler
    try:
        scheduler = create_scheduler(
            invoke_callback=scheduled_recommendation_callback,
            interval_minutes=60
        )
        logger.info("Recommendation scheduler initialized and started")
    except Exception as e:
        logger.error(f"Failed to initialize recommendation scheduler: {e}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
