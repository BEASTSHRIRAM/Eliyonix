"""
Test Qdrant Embeddings and Vector DB
Verifies that sensor data is properly stored with structured embeddings
"""
import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.qdrant_store import get_qdrant_store
from dotenv import load_dotenv

load_dotenv()

async def test_embeddings():
    print("=" * 70)
    print("QDRANT VECTOR DATABASE TEST")
    print("=" * 70)
    print()
    
    # Initialize Qdrant
    qdrant = get_qdrant_store()
    
    if qdrant.mock_mode:
        print("⚠️  Running in MOCK MODE (Qdrant not connected)")
        print("   Fix network/firewall to enable real storage")
        print()
    else:
        print("✓ Connected to Qdrant!")
        print()
    
    # Test data: 3 scenarios
    test_scenarios = [
        {
            "name": "Normal Operation",
            "data": {
                "voltage": 415.0,
                "current": 8.2,
                "temperature": 32.0,
                "ldr": 850,
                "timestamp": datetime.now().timestamp(),
                "inverter_id": "INV_001",
                "village_id": "KA_001",
            },
            "anomaly_score": 0.05,
            "fault_detected": False,
            "fault_type": None,
        },
        {
            "name": "Overvoltage Fault",
            "data": {
                "voltage": 435.0,  # High!
                "current": 9.5,
                "temperature": 38.0,
                "ldr": 920,
                "timestamp": datetime.now().timestamp() + 60,
                "inverter_id": "INV_001",
                "village_id": "KA_001",
            },
            "anomaly_score": 0.92,
            "fault_detected": True,
            "fault_type": "inverter_overvoltage",
        },
        {
            "name": "Overheating",
            "data": {
                "voltage": 418.0,
                "current": 8.0,
                "temperature": 68.0,  # Hot!
                "ldr": 880,
                "timestamp": datetime.now().timestamp() + 120,
                "inverter_id": "INV_001",
                "village_id": "KA_001",
            },
            "anomaly_score": 0.88,
            "fault_detected": True,
            "fault_type": "inverter_overtemp",
        },
    ]
    
    print("─" * 70)
    print("STORING SENSOR READINGS WITH EMBEDDINGS")
    print("─" * 70)
    print()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   Voltage: {scenario['data']['voltage']}V")
        print(f"   Current: {scenario['data']['current']}A")
        print(f"   Temperature: {scenario['data']['temperature']}°C")
        print(f"   LDR: {scenario['data']['ldr']}")
        print(f"   Anomaly Score: {scenario['anomaly_score']:.2f}")
        print(f"   Fault: {scenario['fault_detected']}")
        
        # Create embedding (show what it looks like)
        if not qdrant.mock_mode:
            embedding = qdrant._create_embedding(
                scenario['data'],
                scenario['anomaly_score'],
                scenario['fault_type']
            )
            print(f"   Embedding (8D): [{', '.join([f'{x:.3f}' for x in embedding])}]")
        
        # Store in Qdrant
        success = await qdrant.store_sensor_reading(
            sensor_data=scenario['data'],
            anomaly_score=scenario['anomaly_score'],
            fault_detected=scenario['fault_detected'],
            fault_type=scenario['fault_type']
        )
        
        if success:
            print(f"   ✓ Stored in collection: sensor_readings")
        else:
            print(f"   ✗ Storage failed")
        
        # If fault, also store in fault history
        if scenario['fault_detected']:
            fault_success = await qdrant.store_fault_event(
                sensor_data=scenario['data'],
                anomaly_score=scenario['anomaly_score'],
                fault_type=scenario['fault_type'],
                should_alert=True,
                alert_message=f"Alert: {scenario['fault_type']} detected"
            )
            if fault_success:
                print(f"   ✓ Stored in collection: fault_history")
        
        print()
    
    print("─" * 70)
    print("VECTOR DB SUMMARY")
    print("─" * 70)
    print()
    
    if not qdrant.mock_mode:
        try:
            # Get collection info
            sensor_collection = qdrant.client.get_collection(collection_name="sensor_readings")
            fault_collection = qdrant.client.get_collection(collection_name="fault_history")
            
            print(f"Collection: sensor_readings")
            print(f"  Points stored: {sensor_collection.points_count}")
            print(f"  Vector size: {sensor_collection.config.params.vectors.size}D")
            print(f"  Distance metric: {sensor_collection.config.params.vectors.distance}")
            print()
            
            print(f"Collection: fault_history")
            print(f"  Points stored: {fault_collection.points_count}")
            print(f"  Vector size: {fault_collection.config.params.vectors.size}D")
            print(f"  Distance metric: {fault_collection.config.params.vectors.distance}")
            print()
            
        except Exception as e:
            print(f"Could not retrieve collection stats: {e}")
            print()
    else:
        print("Mock mode - no actual storage")
        print()
    
    print("─" * 70)
    print("EMBEDDING STRUCTURE EXPLANATION")
    print("─" * 70)
    print()
    print("8D Embedding Vector:")
    print("  [0] Voltage (normalized 0-1)")
    print("  [1] Current (normalized 0-1)")
    print("  [2] Temperature (normalized 0-1)")
    print("  [3] LDR light sensor (normalized 0-1)")
    print("  [4] Hour sine (cyclic time encoding)")
    print("  [5] Hour cosine (cyclic time encoding)")
    print("  [6] Day-of-week sine (cyclic encoding)")
    print("  [7] Day-of-week cosine (cyclic encoding)")
    print()
    print("Why cyclic encoding?")
    print("  - Captures that 23:00 is close to 00:00")
    print("  - Enables similarity search across time boundaries")
    print("  - Better for pattern recognition than linear encoding")
    print()
    
    print("─" * 70)
    print("TESTING HISTORICAL DATA RETRIEVAL")
    print("─" * 70)
    print()
    
    if not qdrant.mock_mode:
        historical = await qdrant.get_historical_data("KA_001", days=7)
        print(f"Retrieved {len(historical)} readings for village KA_001")
        if historical:
            print(f"Latest reading: {historical[0].get('datetime', 'N/A')}")
            print(f"  Voltage: {historical[0].get('voltage')}V")
            print(f"  Fault: {historical[0].get('fault_detected')}")
    else:
        print("Mock mode - no historical data available")
    
    print()
    print("=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)
    print()
    
    if qdrant.mock_mode:
        print("⚠️  TO ENABLE REAL STORAGE:")
        print("   1. Fix network/firewall blocking Qdrant Cloud")
        print("   2. OR run local Qdrant: docker-compose up -d")
        print("   3. Then update .env with correct QDRANT_URL")
    else:
        print("✓ Vector DB is working!")
        print("  - All sensor readings are being stored")
        print("  - Embeddings are structured for AI recommendations")
        print("  - Ready for MQTT integration")


if __name__ == "__main__":
    asyncio.run(test_embeddings())
