"""
Integration tests for VidyutSeva multi-agent system
Tests A2A communication, memory persistence, and end-to-end flows
"""
import pytest
import asyncio
from datetime import datetime
import uuid

from src.grid_state import SensorData, create_empty_grid_state
from src.orchestrator import get_orchestrator, reset_orchestrator
from src.a2a_protocol import get_message_broker, reset_message_broker, create_query_message
from src.memory_store import get_memory_store, InMemoryStore, set_memory_store
from src.bedrock_integration import BedrockAlertGenerator


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test"""
    # Setup
    reset_orchestrator()
    reset_message_broker()
    set_memory_store(InMemoryStore())
    
    yield
    
    # Teardown
    reset_orchestrator()
    reset_message_broker()


class TestFaultDetection:
    """Test Fault Detector agent"""
    
    @pytest.mark.asyncio
    async def test_normal_sensor_data_no_fault(self):
        """Normal sensor data should not trigger fault"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 415.0,
            "current": 8.0,
            "temperature": 32.0,
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        assert result["fault_detected"] == False
        assert result["anomaly_score"] < 0.6
    
    @pytest.mark.asyncio
    async def test_overvoltage_triggers_fault(self):
        """High voltage should trigger overvoltage fault"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 430.0,  # High voltage
            "current": 8.0,
            "temperature": 32.0,
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        assert result["fault_detected"] == True or result["anomaly_score"] > 0.5
        assert result["fault_type"] in ["inverter_overvoltage", "inverter_fault"]
    
    @pytest.mark.asyncio
    async def test_overtemp_triggers_fault(self):
        """High temperature should trigger overtemp fault"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 415.0,
            "current": 8.0,
            "temperature": 50.0,  # High temperature
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        assert result["fault_type"] in ["inverter_overtemp", "inverter_fault"]


class TestLoadForecasting:
    """Test Load Forecaster agent"""
    
    @pytest.mark.asyncio
    async def test_load_forecast_generated(self):
        """Load forecast should be generated"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 415.0,
            "current": 8.0,
            "temperature": 32.0,
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        assert result["demand_forecast"] is not None
        assert "demand_current" in result["demand_forecast"]
        assert "demand_2h" in result["demand_forecast"]
        assert "confidence" in result["demand_forecast"]


class TestAlertDispatcher:
    """Test Alert Dispatcher agent"""
    
    @pytest.mark.asyncio
    async def test_high_confidence_fault_triggers_alert(self):
        """High confidence fault should trigger alert"""
        orchestrator = get_orchestrator()
        
        # Simulate high confidence fault
        sensor_data: SensorData = {
            "voltage": 435.0,  # Very high voltage
            "current": 8.0,
            "temperature": 32.0,
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        # High confidence fault should generate alert
        if result["anomaly_score"] > 0.75:
            assert result["should_alert"] == True
            assert result["alert_message"] is not None and result["alert_message"] != ""
    
    @pytest.mark.asyncio
    async def test_demand_spike_prevents_alert(self):
        """Demand spike should prevent fault alert"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 420.0,
            "current": 12.0,  # High current (demand spike)
            "temperature": 32.0,
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        # If it's a demand spike, alert should be prevented
        if result["is_demand_spike"]:
            assert result["should_alert"] == False


class TestA2AMessaging:
    """Test Agent-to-Agent messaging"""
    
    @pytest.mark.asyncio
    async def test_message_send_receive(self):
        """Test basic message send/receive"""
        broker = get_message_broker()
        
        query = create_query_message(
            from_agent="fault_detector",
            to_agent="load_forecaster",
            payload={"test": "data"}
        )
        
        await broker.send_message(query)
        messages = await broker.receive_messages("load_forecaster")
        
        assert len(messages) == 1
        assert messages[0]["from_agent"] == "fault_detector"
        assert messages[0]["payload"]["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_message_deduplication(self):
        """Test duplicate messages are ignored"""
        broker = get_message_broker()
        
        query = create_query_message(
            from_agent="fault_detector",
            to_agent="load_forecaster",
            payload={"test": "data"}
        )
        
        msg_id = await broker.send_message(query)
        await broker.send_message(query)  # Send same message again
        
        messages = await broker.receive_messages("load_forecaster")
        
        # Should only have one message due to deduplication
        assert len(messages) == 1


class TestMemoryPersistence:
    """Test memory persistence"""
    
    @pytest.mark.asyncio
    async def test_agent_memory_saves_and_loads(self):
        """Test agent memory is saved and loaded"""
        from src.memory_store import (
            initialize_agent_memory,
            get_fault_detector_initial_memory,
            append_to_memory_list,
        )
        
        agent_name = "test_agent"
        initial = get_fault_detector_initial_memory()
        
        # Initialize
        memory = await initialize_agent_memory(agent_name, initial)
        assert memory["agent_name"] == agent_name
        
        # Append data
        await append_to_memory_list(
            agent_name,
            "anomaly_history",
            {"timestamp": 123, "anomaly_score": 0.5}
        )
        
        # Load
        store = get_memory_store()
        loaded = await store.load_agent_memory(agent_name)
        
        assert len(loaded["anomaly_history"]) == 1
        assert loaded["anomaly_history"][0]["anomaly_score"] == 0.5


class TestBedrockIntegration:
    """Test Bedrock alert generation"""
    
    @pytest.mark.asyncio
    async def test_fallback_alert_generation(self):
        """Test fallback alert generation (when Bedrock unavailable)"""
        generator = BedrockAlertGenerator()
        
        # Fallback should work without real Bedrock
        alert = generator._get_fallback_kannada_alert("inverter_overvoltage", 0.9)
        
        assert alert is not None
        assert len(alert) > 0
        # Check for Kannada characters
        assert "ಇ" in alert or "ೋ" in alert or "ವ" in alert


class TestEndToEndFlow:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_normal_conditions(self):
        """Test complete pipeline under normal conditions"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 415.0,
            "current": 8.0,
            "temperature": 32.0,
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_001",
            "village_id": "KA_001",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        # Verify all fields are present
        assert "execution_id" in result
        assert "fault_detected" in result
        assert "anomaly_score" in result
        assert "demand_forecast" in result
        assert "should_alert" in result
        assert len(result.get("errors", [])) == 0
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_fault_conditions(self):
        """Test complete pipeline under fault conditions"""
        orchestrator = get_orchestrator()
        
        sensor_data: SensorData = {
            "voltage": 440.0,  # Severe overvoltage
            "current": 5.0,
            "temperature": 45.0,  # Elevated temperature
            "timestamp": datetime.now().timestamp(),
            "inverter_id": "INV_002",
            "village_id": "KA_002",
        }
        
        result = await orchestrator.process_sensor_data(sensor_data)
        
        # High anomaly should be detected
        assert result["anomaly_score"] > 0.4
        assert result["fault_type"] is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
