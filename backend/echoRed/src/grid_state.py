"""
VidyutSeva Grid State Machine Definition
Defines the state passed through the LangGraph pipeline
"""
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class SensorData(TypedDict):
    """Input sensor data from MQTT"""
    voltage: float  # Volts
    current: float  # Amps
    temperature: float  # Celsius
    timestamp: float  # Unix timestamp
    inverter_id: str
    village_id: str


class AnomalyRecord(TypedDict):
    """Historical anomaly record"""
    timestamp: float
    anomaly_score: float
    fault_type: str
    resolved: bool
    a2a_consensus: Optional[str]


class BaselineMetrics(TypedDict):
    """Baseline metrics for anomaly detection"""
    voltage_mean: float
    voltage_std: float
    current_mean: float
    current_std: float
    temp_mean: float
    temp_std: float


class ForecastData(TypedDict):
    """Load forecast data"""
    demand_current: float
    demand_2h: float
    demand_4h: float
    is_demand_spike: bool
    confidence: float
    timestamp: float


class AlertRecord(TypedDict):
    """Historical alert record"""
    timestamp: float
    fault_type: str
    message: str
    recipient: str
    status: str  # "sent", "failed", "confirmed"
    technician_response: Optional[str]


class RecommendationRecord(TypedDict):
    """Recommendation record for a component"""
    timestamp: float
    component: str  # "solar", "fault", "forecast", "alerts", "sensor", "agents"
    text: str
    confidence: float  # 0-1
    status: str  # "ACTION_REQUIRED", "MONITOR", "OPTIMAL"
    retrieved_event_count: int


class A2AMessage(TypedDict):
    """Agent-to-Agent message format"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str  # "query", "response", "consensus_check"
    in_reply_to: Optional[str]
    payload: Dict[str, Any]
    timestamp: float


class GridState(TypedDict):
    """Main state passed through LangGraph"""
    # Input sensor data
    sensor_data: SensorData
    
    # Fault Detector outputs
    fault_detected: bool
    anomaly_score: float
    fault_type: Optional[str]
    fault_detector_memory: Optional[Dict[str, Any]]
    
    # Load Forecaster outputs
    demand_forecast: Optional[ForecastData]
    is_demand_spike: bool
    load_forecaster_memory: Optional[Dict[str, Any]]
    
    # A2A messages
    pending_a2a_messages: List[A2AMessage]
    a2a_responses: Dict[str, A2AMessage]
    
    # Alert Dispatcher outputs
    should_alert: bool
    alert_message: Optional[str]
    alert_language: str  # "kannada", "hindi", "english"
    telegram_status: Optional[Dict[str, Any]]
    alert_dispatcher_memory: Optional[Dict[str, Any]]
    
    # Recommendation Agent outputs
    recommendations: Optional[Dict[str, Dict[str, Any]]]  # component -> recommendation
    recommendation_memory: Optional[Dict[str, Any]]
    
    # Metadata
    execution_id: str
    timestamp: float
    errors: List[str]


class AgentMemory(TypedDict):
    """Agent memory structure stored in RDS"""
    agent_name: str
    baseline_metrics: Optional[BaselineMetrics]
    anomaly_history: List[AnomalyRecord]
    forecast_history: List[ForecastData]
    alerts_sent: List[AlertRecord]
    learned_patterns: Dict[str, Any]
    last_updated: float


# Initialize empty grid state
def create_empty_grid_state(sensor_data: SensorData, execution_id: str) -> GridState:
    """Create an empty grid state with sensor data"""
    return {
        "sensor_data": sensor_data,
        "fault_detected": False,
        "anomaly_score": 0.0,
        "fault_type": None,
        "fault_detector_memory": None,
        "demand_forecast": None,
        "is_demand_spike": False,
        "load_forecaster_memory": None,
        "pending_a2a_messages": [],
        "a2a_responses": {},
        "should_alert": False,
        "alert_message": None,
        "alert_language": "kannada",
        "telegram_status": None,
        "alert_dispatcher_memory": None,
        "recommendations": None,
        "recommendation_memory": None,
        "execution_id": execution_id,
        "timestamp": datetime.now().timestamp(),
        "errors": [],
    }
