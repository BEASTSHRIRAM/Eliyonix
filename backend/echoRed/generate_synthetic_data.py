"""
Generate 7 days of synthetic sensor data and populate Qdrant
Simulates realistic solar inverter behavior with faults
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.qdrant_store import get_qdrant_store
from dotenv import load_dotenv

load_dotenv()


def generate_7_days_data():
    """
    Generate realistic 7-day sensor data
    - Hourly readings (24 * 7 = 168 data points)
    - Solar patterns (high during day, zero at night)
    - Weather variations (cloudy days, rainy days)
    - Random faults (overvoltage, overheating, etc.)
    """
    data_points = []
    start_time = datetime.now() - timedelta(days=7)
    
    # Weather patterns for each day
    weather_patterns = [
        {"type": "sunny", "cloud_factor": 1.0, "rain": False},
        {"type": "sunny", "cloud_factor": 1.0, "rain": False},
        {"type": "partly_cloudy", "cloud_factor": 0.7, "rain": False},
        {"type": "cloudy", "cloud_factor": 0.4, "rain": False},
        {"type": "rainy", "cloud_factor": 0.2, "rain": True},
        {"type": "sunny", "cloud_factor": 1.0, "rain": False},
        {"type": "sunny", "cloud_factor": 0.9, "rain": False},
    ]
    
    for day in range(7):
        weather = weather_patterns[day]
        
        for hour in range(24):
            timestamp = start_time + timedelta(days=day, hours=hour)
            
            # Solar irradiance pattern (bell curve during day)
            if 6 <= hour <= 18:
                # Daytime: peak at 12:00
                solar_factor = math.sin(math.pi * (hour - 6) / 12)
                solar_factor *= weather["cloud_factor"]
            else:
                # Nighttime: no solar
                solar_factor = 0.0
            
            # Base values
            base_voltage = 415.0
            base_current = 8.0
            base_temp = 30.0
            base_ldr = 800
            
            # Calculate realistic values
            voltage = base_voltage + (solar_factor * 10) + random.uniform(-3, 3)
            current = base_current * solar_factor + random.uniform(-0.5, 0.5)
            temperature = base_temp + (solar_factor * 15) + random.uniform(-2, 2)
            ldr = int(base_ldr * solar_factor + random.uniform(-50, 50))
            
            # Inject faults randomly (5% chance)
            fault_detected = False
            fault_type = None
            anomaly_score = random.uniform(0.01, 0.15)  # Normal range
            
            if random.random() < 0.05:  # 5% fault rate
                fault_detected = True
                fault_choice = random.choice([
                    "overvoltage", "undervoltage", "overtemp", "dust"
                ])
                
                if fault_choice == "overvoltage":
                    voltage += random.uniform(15, 25)
                    fault_type = "inverter_overvoltage"
                    anomaly_score = random.uniform(0.75, 0.95)
                    
                elif fault_choice == "undervoltage":
                    voltage -= random.uniform(20, 30)
                    fault_type = "inverter_undervoltage"
                    anomaly_score = random.uniform(0.70, 0.90)
                    
                elif fault_choice == "overtemp":
                    temperature += random.uniform(25, 35)
                    fault_type = "inverter_overtemp"
                    anomaly_score = random.uniform(0.80, 0.95)
                    
                elif fault_choice == "dust":
                    # Dust reduces efficiency
                    current *= 0.6
                    ldr = int(ldr * 0.7)
                    fault_type = "inverter_fault"
                    anomaly_score = random.uniform(0.60, 0.75)
            
            # Rainy day effects
            if weather["rain"] and 6 <= hour <= 18:
                current *= 0.5  # Reduced output
                ldr = int(ldr * 0.3)
                temperature -= 5
            
            data_point = {
                "sensor_data": {
                    "voltage": max(0, voltage),
                    "current": max(0, current),
                    "temperature": max(0, temperature),
                    "ldr": max(0, min(1023, ldr)),
                    "timestamp": timestamp.timestamp(),
                    "inverter_id": "INV_001",
                    "village_id": "KA_001",
                },
                "anomaly_score": anomaly_score,
                "fault_detected": fault_detected,
                "fault_type": fault_type,
                "weather": weather["type"],
                "hour": hour,
                "day": day,
            }
            
            data_points.append(data_point)
    
    return data_points


async def populate_qdrant():
    """Populate Qdrant with 7 days of synthetic data"""
    print("=" * 70)
    print("GENERATING 7 DAYS OF SYNTHETIC SENSOR DATA")
    print("=" * 70)
    print()
    
    # Generate data
    print("Generating realistic sensor readings...")
    data_points = generate_7_days_data()
    print(f"✓ Generated {len(data_points)} data points (7 days × 24 hours)")
    print()
    
    # Statistics
    faults = [d for d in data_points if d["fault_detected"]]
    print(f"Data Summary:")
    print(f"  Total readings: {len(data_points)}")
    print(f"  Fault events: {len(faults)}")
    print(f"  Fault rate: {len(faults)/len(data_points)*100:.1f}%")
    print()
    
    # Fault breakdown
    fault_types = {}
    for f in faults:
        ft = f["fault_type"]
        fault_types[ft] = fault_types.get(ft, 0) + 1
    
    print("Fault Types:")
    for ft, count in fault_types.items():
        print(f"  {ft}: {count}")
    print()
    
    # Connect to Qdrant
    print("─" * 70)
    print("STORING IN QDRANT VECTOR DATABASE")
    print("─" * 70)
    print()
    
    qdrant = get_qdrant_store()
    
    if qdrant.mock_mode:
        print("⚠️  MOCK MODE - Data not actually stored")
        print("   Fix Qdrant connection to enable real storage")
        print()
        return
    
    print("✓ Connected to Qdrant")
    print()
    
    # Store all data points
    stored_count = 0
    fault_stored_count = 0
    
    for i, dp in enumerate(data_points):
        # Store sensor reading
        success = await qdrant.store_sensor_reading(
            sensor_data=dp["sensor_data"],
            anomaly_score=dp["anomaly_score"],
            fault_detected=dp["fault_detected"],
            fault_type=dp["fault_type"]
        )
        
        if success:
            stored_count += 1
        
        # Store fault event if detected
        if dp["fault_detected"]:
            fault_success = await qdrant.store_fault_event(
                sensor_data=dp["sensor_data"],
                anomaly_score=dp["anomaly_score"],
                fault_type=dp["fault_type"],
                should_alert=True,
                alert_message=f"Alert: {dp['fault_type']} detected"
            )
            if fault_success:
                fault_stored_count += 1
        
        # Progress indicator
        if (i + 1) % 24 == 0:
            day = (i + 1) // 24
            print(f"  Day {day}/7 complete ({i+1}/{len(data_points)} readings)")
    
    print()
    print("─" * 70)
    print("STORAGE COMPLETE")
    print("─" * 70)
    print()
    print(f"✓ Stored {stored_count} sensor readings in 'sensor_readings' collection")
    print(f"✓ Stored {fault_stored_count} fault events in 'fault_history' collection")
    print()
    
    # Verify collections
    try:
        sensor_col = qdrant.client.get_collection("sensor_readings")
        fault_col = qdrant.client.get_collection("fault_history")
        
        print("Collection Statistics:")
        print(f"  sensor_readings: {sensor_col.points_count} points")
        print(f"  fault_history: {fault_col.points_count} points")
        print()
    except Exception as e:
        print(f"Could not retrieve stats: {e}")
        print()
    
    print("=" * 70)
    print("SYNTHETIC DATA GENERATION COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run 'python run_local.py' to test real-time agent processing")
    print("  2. Use recommendation API to get AI suggestions based on this data")
    print()


if __name__ == "__main__":
    asyncio.run(populate_qdrant())
