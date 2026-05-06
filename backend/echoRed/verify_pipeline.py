"""
Verify Bedrock AgentCore Pipeline + Qdrant Integration
Tests that fault detector stores data in vector DB
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.qdrant_store import get_qdrant_store
from src.orchestrator import get_orchestrator
from src.grid_state import SensorData
from dotenv import load_dotenv

load_dotenv()


async def verify_pipeline():
    """Verify the complete pipeline: Agents → Qdrant"""
    
    print("=" * 70)
    print("BEDROCK AGENTCORE PIPELINE VERIFICATION")
    print("=" * 70)
    print()
    
    # Step 1: Check Qdrant connection
    print("Step 1: Checking Qdrant connection...")
    qdrant = get_qdrant_store()
    
    if qdrant.mock_mode:
        print("❌ FAILED: Qdrant is in mock mode")
        print("   Fix: Ensure Qdrant is running and .env is configured")
        return False
    
    print("✓ Qdrant connected")
    print()
    
    # Step 2: Get initial collection counts
    print("Step 2: Getting initial collection state...")
    try:
        sensor_col = qdrant.client.get_collection("sensor_readings")
        fault_col = qdrant.client.get_collection("fault_history")
        
        initial_sensor_count = sensor_col.points_count
        initial_fault_count = fault_col.points_count
        
        print(f"✓ sensor_readings: {initial_sensor_count} points")
        print(f"✓ fault_history: {initial_fault_count} points")
    except Exception as e:
        print(f"⚠️  Collections not initialized yet: {e}")
        initial_sensor_count = 0
        initial_fault_count = 0
    
    print()
    
    # Step 3: Run agent pipeline with test data
    print("Step 3: Running Bedrock AgentCore pipeline...")
    print("─" * 70)
    
    orchestrator = get_orchestrator()
    
    # Test 1: Normal operation
    print()
    print("Test 1: Normal Operation")
    print("─" * 70)
    
    normal_sensor_data: SensorData = {
        "voltage": 415.0,
        "current": 8.0,
        "temperature": 32.0,
        "timestamp": datetime.now().timestamp(),
        "inverter_id": "INV_TEST_001",
        "village_id": "KA_TEST",
    }
    
    result1 = await orchestrator.process_sensor_data(normal_sensor_data)
    
    print(f"✓ Execution ID: {result1['execution_id']}")
    print(f"  Fault Detected: {result1['fault_detected']}")
    print(f"  Anomaly Score: {result1['anomaly_score']:.2f}")
    print(f"  Should Alert: {result1.get('should_alert', False)}")
    
    # Test 2: Fault condition (overvoltage)
    print()
    print("Test 2: Fault Condition (Overvoltage)")
    print("─" * 70)
    
    fault_sensor_data: SensorData = {
        "voltage": 425.0,  # High voltage
        "current": 8.5,
        "temperature": 35.0,
        "timestamp": datetime.now().timestamp(),
        "inverter_id": "INV_TEST_001",
        "village_id": "KA_TEST",
    }
    
    result2 = await orchestrator.process_sensor_data(fault_sensor_data)
    
    print(f"✓ Execution ID: {result2['execution_id']}")
    print(f"  Fault Detected: {result2['fault_detected']}")
    print(f"  Anomaly Score: {result2['anomaly_score']:.2f}")
    print(f"  Fault Type: {result2.get('fault_type', 'N/A')}")
    print(f"  Should Alert: {result2.get('should_alert', False)}")
    
    # Test 3: Another fault (overheating)
    print()
    print("Test 3: Fault Condition (Overheating)")
    print("─" * 70)
    
    overheat_sensor_data: SensorData = {
        "voltage": 415.0,
        "current": 8.0,
        "temperature": 65.0,  # High temperature
        "timestamp": datetime.now().timestamp(),
        "inverter_id": "INV_TEST_001",
        "village_id": "KA_TEST",
    }
    
    result3 = await orchestrator.process_sensor_data(overheat_sensor_data)
    
    print(f"✓ Execution ID: {result3['execution_id']}")
    print(f"  Fault Detected: {result3['fault_detected']}")
    print(f"  Anomaly Score: {result3['anomaly_score']:.2f}")
    print(f"  Fault Type: {result3.get('fault_type', 'N/A')}")
    print(f"  Should Alert: {result3.get('should_alert', False)}")
    
    print()
    print("─" * 70)
    
    # Step 4: Verify data was stored in Qdrant
    print()
    print("Step 4: Verifying data storage in Qdrant...")
    print("─" * 70)
    
    # Wait a moment for async storage to complete
    await asyncio.sleep(2)
    
    try:
        sensor_col = qdrant.client.get_collection("sensor_readings")
        fault_col = qdrant.client.get_collection("fault_history")
        
        final_sensor_count = sensor_col.points_count
        final_fault_count = fault_col.points_count
        
        sensor_added = final_sensor_count - initial_sensor_count
        fault_added = final_fault_count - initial_fault_count
        
        print(f"✓ sensor_readings: {final_sensor_count} points (+{sensor_added} new)")
        print(f"✓ fault_history: {final_fault_count} points (+{fault_added} new)")
        print()
        
        # Verify expected storage
        success = True
        
        if sensor_added < 3:
            print(f"⚠️  WARNING: Expected 3 sensor readings, but only {sensor_added} were stored")
            success = False
        else:
            print(f"✓ All 3 sensor readings stored successfully")
        
        # We expect at least 1-2 faults (overvoltage and overheating)
        if fault_added < 1:
            print(f"⚠️  WARNING: Expected fault events, but only {fault_added} were stored")
            success = False
        else:
            print(f"✓ Fault events stored successfully ({fault_added} faults)")
        
        print()
        
        # Step 5: Verify embeddings
        print("Step 5: Verifying 8D embeddings...")
        print("─" * 70)
        
        # Retrieve a sample point to check embedding structure
        results = qdrant.client.scroll(
            collection_name="sensor_readings",
            limit=1,
            with_vectors=True
        )
        
        if results[0]:
            sample_point = results[0][0]
            vector = sample_point.vector
            
            if len(vector) == 8:
                print(f"✓ Embedding structure correct: 8 dimensions")
                print(f"  Vector sample: [{vector[0]:.3f}, {vector[1]:.3f}, {vector[2]:.3f}, {vector[3]:.3f}, ...]")
                print(f"  Structure: [v_norm, i_norm, t_norm, ldr_norm, hour_sin, hour_cos, dow_sin, dow_cos]")
            else:
                print(f"⚠️  WARNING: Expected 8D vector, got {len(vector)}D")
                success = False
        else:
            print("⚠️  WARNING: Could not retrieve sample point")
            success = False
        
        print()
        print("=" * 70)
        
        if success:
            print("✅ PIPELINE VERIFICATION PASSED")
            print("=" * 70)
            print()
            print("Summary:")
            print(f"  • Bedrock AgentCore pipeline: ✓ Working")
            print(f"  • Fault detector: ✓ Detecting faults")
            print(f"  • Qdrant storage: ✓ Storing data")
            print(f"  • 8D embeddings: ✓ Correct structure")
            print(f"  • Total sensor readings: {final_sensor_count}")
            print(f"  • Total fault events: {final_fault_count}")
            print()
            print("Next steps:")
            print("  1. Test recommendation API:")
            print("     curl http://localhost:8080/recommendations/ai?village_id=KA_TEST")
            print()
            print("  2. Run frontend to see recommendations:")
            print("     cd frontend && npm run dev")
            print()
        else:
            print("⚠️  PIPELINE VERIFICATION INCOMPLETE")
            print("=" * 70)
            print()
            print("Some issues detected. Check warnings above.")
            print()
        
        return success
        
    except Exception as e:
        print(f"❌ FAILED: Could not verify storage: {e}")
        print()
        print("This might mean:")
        print("  • Collections not created")
        print("  • Storage failed silently")
        print("  • Qdrant connection lost")
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_pipeline())
    sys.exit(0 if success else 1)
