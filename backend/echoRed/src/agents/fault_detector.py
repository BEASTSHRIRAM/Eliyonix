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
        self.is_trained = False
        self._train_with_default_data()
    
    def _train_with_default_data(self):
        """Train the model with default normal sensor data"""
        # Generate synthetic normal data for training
        # Normal voltage range: 410-420V
        # Normal current range: 5-12A
        # Normal temperature range: 20-40°C
        normal_data = np.array([
            [415, 8, 30],  # Normal conditions
            [414, 7.5, 28],
            [416, 8.5, 32],
            [413, 7, 25],
            [418, 9, 35],
            [412, 6.5, 22],
            [417, 8.2, 31],
            [415.5, 7.8, 29],
            [414.5, 8.3, 33],
            [416.5, 7.2, 27],
            [413.5, 8.7, 34],
            [418.5, 6.8, 24],
            [415.2, 8.1, 30],
            [414.8, 7.9, 29],
            [416.2, 8.4, 32],
            [412.5, 7.1, 26],
            [417.5, 8.8, 36],
            [415.8, 7.3, 28],
            [413.2, 8.9, 38],
            [418.2, 6.9, 23],
        ])
        
        self.isolation_forest.fit(normal_data)
        self.is_trained = True
        logger.info("FaultDetector trained with default normal sensor data")
    
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
        Raw scores: -1 = anomaly, 0 = normal
        Convert so 0 = normal, 1 = anomaly
        """
        # IsolationForest returns anomaly scores: -1 is anomaly, 0+ is normal
        # If raw_score < -0.5, it's likely anomalous
        if raw_score < -0.5:
            return min(1.0, abs(raw_score) * 2)  # Scale anomaly scores
        else:
            return 0.0  # Normal data returns 0
    
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
