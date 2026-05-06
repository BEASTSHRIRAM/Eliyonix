# AI Recommendation System - Complete Guide

## Overview

The AI Recommendation System uses **semantic search on Qdrant vector database** to analyze 7 days of historical sensor data and provide intelligent, context-aware suggestions to farmers.

## Architecture

```
ESP32/Raspberry Pi → MQTT → Backend Agents → Qdrant Vector DB
                                                    ↓
                                            Recommendation Engine
                                                    ↓
                                            Frontend Dashboard
```

## Features

### 1. **8-Dimensional Embeddings**
Each sensor reading is stored as an 8D vector:
- `[voltage_norm, current_norm, temp_norm, ldr_norm, hour_sin, hour_cos, dow_sin, dow_cos]`
- Uses cyclic encoding for time (captures that 23:00 is close to 00:00)
- Enables semantic similarity search

### 2. **Two Qdrant Collections**
- **`sensor_readings`**: ALL readings (faulty or not) - complete history
- **`fault_history`**: Only fault events for pattern learning

### 3. **AI Analysis**
The recommendation engine analyzes:
- Fault rates over 7 days
- Performance trends (improving/declining/stable)
- Fault type patterns (overvoltage, overheating, etc.)
- Time-based patterns (day vs night faults)
- Weather impact (rainy days, cloudy days)
- System efficiency scores

### 4. **Prioritized Recommendations**
- **High Priority**: Critical issues requiring immediate action
- **Medium Priority**: Performance optimization opportunities
- **Low Priority**: Preventive maintenance and monitoring

## Setup Instructions

### Step 1: Fix Qdrant Connection

**Current Issue**: Network/firewall blocking Qdrant Cloud connection (Error 10054)

**Solutions** (choose one):

#### Option A: Fix Network/Firewall
```bash
# Check if you can access Qdrant dashboard
# Visit: https://cloud.qdrant.io/

# If blocked, try:
# 1. Disable VPN/proxy temporarily
# 2. Check Windows Firewall settings
# 3. Try mobile hotspot
```

#### Option B: Run Local Qdrant (Recommended for Development)
```bash
# Start local Qdrant with Docker
cd backend/echoRed
docker-compose up -d

# Update .env file
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local

# Verify connection
python test_qdrant.py
```

### Step 2: Generate 7 Days of Synthetic Data

Once Qdrant is connected:

```bash
cd backend/echoRed
python generate_synthetic_data.py
```

This will:
- Generate 168 hourly readings (7 days × 24 hours)
- Simulate realistic solar patterns (day/night cycles)
- Include weather variations (sunny, cloudy, rainy)
- Inject random faults (5% rate)
- Store everything in Qdrant with 8D embeddings

**Expected Output**:
```
✓ Generated 168 data points (7 days × 24 hours)
  Total readings: 168
  Fault events: 8
  Fault rate: 4.8%

✓ Stored 168 sensor readings in 'sensor_readings' collection
✓ Stored 8 fault events in 'fault_history' collection
```

### Step 3: Test Embeddings

```bash
python test_embeddings.py
```

Verifies that:
- Embeddings are correctly structured (8 dimensions)
- Cyclic time encoding works
- Similar readings have high cosine similarity

### Step 4: Run Backend

```bash
python run_local.py
```

Or for production:
```bash
cd backend/echoRed
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### Step 5: Test Recommendation API

```bash
# Get AI recommendations for village KA_001
curl http://localhost:8080/recommendations/ai?village_id=KA_001
```

**Example Response**:
```json
{
  "status": "success",
  "village_id": "KA_001",
  "analysis_period": "7 days",
  "data_points_analyzed": 168,
  "analysis": {
    "total_readings": 168,
    "fault_rate": 0.048,
    "fault_count": 8,
    "fault_types": {
      "inverter_overtemp": 3,
      "inverter_overvoltage": 2,
      "inverter_fault": 3
    },
    "avg_voltage": 415.2,
    "avg_temperature": 35.8,
    "performance_trend": "stable",
    "efficiency_score": 92.3
  },
  "recommendations": [
    {
      "priority": "high",
      "category": "cooling",
      "title": "Overheating Issues",
      "description": "Inverter overheating detected 3 times in past 7 days.",
      "action": "Check ventilation, clean cooling fans, verify ambient temperature",
      "confidence": 0.90,
      "impact": "High - reduces lifespan and efficiency"
    },
    {
      "priority": "medium",
      "category": "electrical",
      "title": "Voltage Regulation Issues",
      "description": "Overvoltage events: 2 times. May indicate grid instability.",
      "action": "Install voltage stabilizer or check grid connection",
      "confidence": 0.85,
      "impact": "Medium - can damage equipment"
    }
  ]
}
```

### Step 6: Frontend Integration

The frontend already has recommendation buttons on each dashboard card. They will automatically call the new API endpoint.

**Test in Browser**:
1. Start frontend: `cd frontend && npm run dev`
2. Open http://localhost:5173
3. Click "Recommendation" button on any dashboard card
4. View AI-powered suggestions based on historical patterns

## API Endpoints

### 1. Get AI Recommendations
```
GET /recommendations/ai?village_id=KA_001
POST /recommendations/ai
```

**Query Parameters**:
- `village_id` (optional): Village ID (default: KA_001)

**POST Body** (optional):
```json
{
  "current_sensor_data": {
    "voltage": 415.0,
    "current": 8.0,
    "temperature": 32.0,
    "ldr": 800
  }
}
```

**Response**: See example above

### 2. Get Component Recommendation
```
GET /recommendations/{component}
```

Components: `solar`, `fault`, `forecast`, `alerts`, `sensor`, `agents`

### 3. Get Recommendation History
```
GET /recommendations/history?component=solar&limit=50
```

### 4. Trigger Manual Recommendation
```
POST /recommendations/trigger
```

## How It Works

### 1. Data Collection
```python
# ESP32 → MQTT → Backend
sensor_data = {
    "voltage": 415.0,
    "current": 8.0,
    "temperature": 32.0,
    "ldr": 800,
    "timestamp": timestamp,
    "inverter_id": "INV_001",
    "village_id": "KA_001"
}

# Stored in Qdrant with 8D embedding
embedding = [
    voltage_norm,      # Normalized voltage
    current_norm,      # Normalized current
    temp_norm,         # Normalized temperature
    ldr_norm,          # Normalized light sensor
    sin(2π * hour/24), # Hour (cyclic)
    cos(2π * hour/24),
    sin(2π * dow/7),   # Day of week (cyclic)
    cos(2π * dow/7)
]
```

### 2. Semantic Search
```python
# When user clicks "Recommendation" button
# Engine retrieves 7 days of similar patterns
historical_data = qdrant.get_historical_data(village_id, days=7)

# Analyzes patterns
analysis = {
    "fault_rate": 0.048,
    "performance_trend": "stable",
    "efficiency_score": 92.3,
    "fault_types": {...}
}
```

### 3. AI Recommendation Generation
```python
# Based on analysis, generates prioritized recommendations
if analysis["fault_rate"] > 0.10:
    recommendations.append({
        "priority": "high",
        "category": "maintenance",
        "title": "High Fault Rate Detected",
        "action": "Schedule technician visit within 24 hours",
        "confidence": 0.95
    })
```

## Real Hardware Integration

### ESP32 → Raspberry Pi → Backend

```python
# On Raspberry Pi (MQTT subscriber)
import paho.mqtt.client as mqtt
import requests

def on_message(client, userdata, msg):
    sensor_data = json.loads(msg.payload)
    
    # Send to backend
    response = requests.post(
        "http://backend:8080/invoke",
        json={"sensor_data": sensor_data}
    )
    
    # Backend automatically stores in Qdrant
    # Agents process and detect faults
    # Recommendations updated in real-time

mqtt_client = paho.mqtt.client.Client()
mqtt_client.on_message = on_message
mqtt_client.connect("mqtt_broker", 1883)
mqtt_client.subscribe("village/KA_001/sensors")
mqtt_client.loop_forever()
```

## Troubleshooting

### Issue: "Mock mode - Data not actually stored"
**Solution**: Fix Qdrant connection (see Step 1)

### Issue: "No historical data available"
**Solution**: Run `python generate_synthetic_data.py` to populate data

### Issue: "Recommendations not updating"
**Solution**: Check scheduler status at `/scheduler/status`

### Issue: "Low confidence scores"
**Solution**: Need more historical data (run system for longer or generate more synthetic data)

## Next Steps

1. **Fix Qdrant Connection** (critical blocker)
2. **Generate Synthetic Data** (populate 7 days)
3. **Test Recommendation API** (verify it works)
4. **Connect Real Hardware** (ESP32 → MQTT → Backend)
5. **Monitor in Production** (dashboard shows real-time recommendations)

## Benefits

✅ **Pattern Recognition**: AI learns from historical data  
✅ **Proactive Alerts**: Detects issues before they become critical  
✅ **Farmer-Friendly**: Simple recommendations in plain language  
✅ **Context-Aware**: Considers weather, time of day, seasonal patterns  
✅ **Confidence Scores**: Shows how certain the AI is about each recommendation  
✅ **Prioritized Actions**: High/medium/low priority for decision-making  

## Example Use Cases

### Use Case 1: Rainy Season
```
Analysis: 3 days of low output due to rain
Recommendation: "Weather Impact - High daytime fault rate suggests 
weather-related issues. Monitor weather patterns, consider battery 
backup for cloudy days."
```

### Use Case 2: Overheating Pattern
```
Analysis: Inverter temperature >60°C during peak hours
Recommendation: "Overheating Issues - Check ventilation, clean 
cooling fans, verify ambient temperature. High priority."
```

### Use Case 3: Declining Performance
```
Analysis: Power output decreased 15% over 7 days
Recommendation: "Declining Performance - Clean solar panels, 
check for dust/debris, inspect wiring. Medium priority."
```

---

**Ready to proceed?** Fix the Qdrant connection and run the synthetic data generator!
