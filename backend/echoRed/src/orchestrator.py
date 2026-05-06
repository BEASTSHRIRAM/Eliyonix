"""
VidyutSeva LangGraph Orchestration
Builds and manages the multi-agent state machine
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any, Optional
import logging
import uuid

from .grid_state import GridState, create_empty_grid_state, SensorData
from .agents import (
    fault_detector_node,
    load_forecaster_node,
    alert_dispatcher_node,
    recommendation_agent_node,
)
from .qdrant_store import get_qdrant_store

logger = logging.getLogger(__name__)


class VidyutSevaOrchestrator:
    """Orchestrates the VidyutSeva multi-agent system"""
    
    def __init__(self):
        self.graph = self._build_graph()
        self.compiled_pipeline = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        graph = StateGraph(GridState)
        
        # Add nodes
        graph.add_node("fault_detector", fault_detector_node)
        graph.add_node("load_forecaster", load_forecaster_node)
        graph.add_node("alert_dispatcher", alert_dispatcher_node)
        graph.add_node("recommendation_agent", recommendation_agent_node)
        
        # Add edges
        graph.add_edge("fault_detector", "load_forecaster")
        graph.add_edge("load_forecaster", "alert_dispatcher")
        graph.add_edge("alert_dispatcher", "recommendation_agent")
        graph.add_edge("recommendation_agent", END)
        
        # Set entry point
        graph.set_entry_point("fault_detector")
        
        logger.info("Built VidyutSeva LangGraph")
        return graph
    
    async def process_sensor_data(self, sensor_data: SensorData) -> GridState:
        """
        Process sensor data through the pipeline
        
        Args:
            sensor_data: Sensor readings from MQTT
        
        Returns:
            Final state with alert decision and message
        """
        execution_id = str(uuid.uuid4())
        initial_state = create_empty_grid_state(sensor_data, execution_id)
        
        logger.info(f"Starting execution {execution_id} for {sensor_data['village_id']}")
        
        # Run the pipeline
        result = await self.compiled_pipeline.ainvoke(initial_state)
        
        # Store data in Qdrant after pipeline completes
        try:
            qdrant = get_qdrant_store()
            
            # Store sensor reading (all readings, faulty or not)
            await qdrant.store_sensor_reading(
                sensor_data=sensor_data,
                anomaly_score=result.get("anomaly_score", 0.0),
                fault_detected=result.get("fault_detected", False),
                fault_type=result.get("fault_type")
            )
            
            # Store fault event if detected
            if result.get("fault_detected") and result.get("should_alert"):
                await qdrant.store_fault_event(
                    sensor_data=sensor_data,
                    anomaly_score=result.get("anomaly_score", 0.0),
                    fault_type=result.get("fault_type", "unknown"),
                    should_alert=result.get("should_alert", False),
                    alert_message=result.get("alert_message", "")
                )
                logger.info(f"Stored fault event in Qdrant: {result.get('fault_type')}")
            
            logger.info(f"Stored sensor reading in Qdrant for {sensor_data['village_id']}")
            
        except Exception as e:
            logger.error(f"Failed to store in Qdrant: {e}")
            # Don't fail the pipeline if storage fails
        
        logger.info(
            f"Execution {execution_id} complete. "
            f"Alert: {result.get('should_alert', False)}, "
            f"Message: {result.get('alert_message', 'N/A')}"
        )
        
        return result
    
    def visualize_graph(self) -> str:
        """Generate ASCII visualization of the graph"""
        try:
            return self.graph.get_graph().draw_ascii()
        except Exception as e:
            logger.warning(f"Could not visualize graph: {e}")
            return "Unable to generate visualization"


# Global orchestrator instance
_orchestrator: Optional[VidyutSevaOrchestrator] = None


def get_orchestrator() -> VidyutSevaOrchestrator:
    """Get or create the global orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = VidyutSevaOrchestrator()
    return _orchestrator


def reset_orchestrator():
    """Reset the orchestrator (for testing)"""
    global _orchestrator
    _orchestrator = None


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        orchestrator = get_orchestrator()
        
        # Test with sample sensor data
        test_data: SensorData = {
            "voltage": 425.0,  # High voltage - should trigger overvoltage fault
            "current": 8.5,
            "temperature": 35.0,
            "timestamp": 1234567890.0,
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(test_data)
        
        print(f"\n✓ Execution Complete")
        print(f"  Fault Detected: {result['fault_detected']}")
        print(f"  Anomaly Score: {result['anomaly_score']:.2f}")
        print(f"  Fault Type: {result['fault_type']}")
        print(f"  Demand Spike: {result['is_demand_spike']}")
        print(f"  Should Alert: {result['should_alert']}")
        print(f"  Alert Message: {result['alert_message']}")
    
    asyncio.run(demo())
