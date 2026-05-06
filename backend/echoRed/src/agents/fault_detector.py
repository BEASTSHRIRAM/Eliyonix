"""
Fault Detector Agent
Detects anomalies in solar inverter data using Isolation Forest
"""
from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

from ..grid_state import GridState, SensorData, AnomalyRecord
from ..a2a_protocol import get_message_broker, create_query_message
from ..memory_store import (
    get_memory_store,
    initialize_agent_memory,
    append_to_memory_list,
    get_fault_detector_initial_memory,
)

logger = logging.getLogger(__name__)


class FaultDetector:
    """Detects faults in solar inverter data"""
    
    AGENT_NAME = "fault_detector"
    ANOMALY_THRESHOLD = 0.6
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100,
        )
        self.memory: Dict[str, Any] = {}
    
    async def initialize(self):
        """Initialize agent memory"""
        initial_memory = get_fault_detector_initial_memory()
        self.memory = await initialize_agent_memory(self.AGENT_NAME, initial_memory)
        logger.info(f"Initialized {self.AGENT_NAME}")
    
    async def execute(self, state: GridState) -> GridState:
        """Execute fault detection"""
        try:
            sensor_data = state["sensor_data"]
            
            # Extract features
            features = np.array([
                [sensor_data["voltage"], sensor_data["current"], sensor_data["temperature"]]
            ])
            
            # Calculate anomaly score (0-1)
            raw_score = self.isolation_forest.score_samples(features)[0]
            anomaly_score = self._normalize_score(raw_score)
            
            # Determine fault type and whether it's detected
            fault_type = self._classify_fault(sensor_data, anomaly_score)
            fault_detected = anomaly_score > self.ANOMALY_THRESHOLD
            
            logger.info(
                f"Fault Detection: score={anomaly_score:.2f}, "
                f"fault_detected={fault_detected}, fault_type={fault_type}"
            )
            
            # Send A2A query to Load Forecaster
            if fault_detected:
                await self._send_a2a_query(sensor_data, anomaly_score, fault_type)
            
            # Update memory
            await append_to_memory_list(
                self.AGENT_NAME,
                "anomaly_history",
                {
                    "timestamp": sensor_data["timestamp"],
                    "anomaly_score": anomaly_score,
                    "fault_type": fault_type,
                    "resolved": False,
                    "a2a_consensus": None,
                }
            )
            
            # Update state
            state["fault_detected"] = fault_detected
            state["anomaly_score"] = anomaly_score
            state["fault_type"] = fault_type
            state["fault_detector_memory"] = self.memory
            
            return state
            
        except Exception as e:
            logger.error(f"Error in fault detection: {e}")
            state["errors"].append(f"Fault detector error: {str(e)}")
            return state
    
    def _normalize_score(self, raw_score: float) -> float:
        """
        Normalize Isolation Forest score to 0-1 range
        Raw scores are negative; more negative = more anomalous
        """
        # Approximate transformation: raw scores typically range from -0.1 to 0.1
        # Map to 0-1 with 0 being normal, 1 being highly anomalous
        normalized = max(0, min(1, 1 - (raw_score + 0.1)))
        return normalized
    
    def _classify_fault(self, sensor_data: SensorData, anomaly_score: float) -> str:
        """Classify the type of fault based on sensor readings"""
        voltage = sensor_data["voltage"]
        current = sensor_data["current"]
        temperature = sensor_data["temperature"]
        
        # Thresholds
        NORMAL_VOLTAGE = (410, 420)
        NORMAL_TEMP = (20, 40)
        
        if voltage > NORMAL_VOLTAGE[1]:
            return "inverter_overvoltage"
        elif voltage < NORMAL_VOLTAGE[0]:
            return "inverter_undervoltage"
        elif temperature > NORMAL_TEMP[1]:
            return "inverter_overtemp"
        elif temperature < NORMAL_TEMP[0]:
            return "inverter_undertemp"
        elif current > 15:
            return "inverter_overcurrent"
        else:
            return "inverter_fault"
    
    async def _send_a2a_query(self, sensor_data: SensorData, anomaly_score: float, fault_type: str):
        """Send A2A query to Load Forecaster"""
        broker = get_message_broker()
        
        query = create_query_message(
            from_agent=self.AGENT_NAME,
            to_agent="load_forecaster",
            payload={
                "anomaly_score": anomaly_score,
                "fault_type": fault_type,
                "timestamp": sensor_data["timestamp"],
                "sensor_data": {
                    "voltage": sensor_data["voltage"],
                    "current": sensor_data["current"],
                    "temperature": sensor_data["temperature"],
                },
                "query": "Is this anomaly a demand spike or an actual fault?",
            }
        )
        
        await broker.send_message(query)
        logger.info(f"Sent A2A query to load_forecaster: {query['message_id']}")


async def fault_detector_node(state: GridState) -> GridState:
    """LangGraph node for Fault Detector"""
    detector = FaultDetector()
    await detector.initialize()
    return await detector.execute(state)
