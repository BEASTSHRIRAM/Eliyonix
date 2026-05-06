# VidyutSeva Quick Start Guide

## What You've Built

A production-grade **multi-agent AI system** for rural grid modernization that:
- Detects solar inverter faults with Isolation Forest
- Forecasts electrical demand to avoid false alarms
- Generates localized alerts in Kannada/Hindi via AWS Bedrock
- Uses LangGraph for agent orchestration
- Communicates between agents via A2A protocol
- Persists decisions in memory (in-memory or RDS)

---

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd /workspaces/Eliyonix/backend/echoRed

# Install required packages
pip install scikit-learn numpy psycopg2-binary fastapi uvicorn

# Or use uv
uv pip install scikit-learn numpy psycopg2-binary fastapi uvicorn
```

### Step 2: Run Tests

```bash
# Run all integration tests
pytest test/test_vidyutseva.py -v

# Should see ~15 tests pass
# ✓ Normal sensor data doesn't trigger fault
# ✓ Overvoltage triggers fault
# ✓ Load forecast is generated
# ✓ Demand spike prevents alerts
# ... and more
```

### Step 3: Start Local Development Server

```bash
# Make sure you have AWS credentials configured
aws configure

# Start the Bedrock AgentCore dev server
agentcore dev

# You should see:
# "INFO:     Uvicorn running on http://0.0.0.0:8000"
# "INFO:     Application startup complete"
```

### Step 4: Send Your First Sensor Data (New Terminal)

```bash
# Test normal conditions
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_data": {
      "voltage": 415.0,
      "current": 8.0,
      "temperature": 32.0,
      "timestamp": 1234567890,
      "inverter_id": "INV_001",
      "village_id": "KA_001"
    }
  }'

# Expected response:
# {
#   "execution_id": "uuid",
#   "should_alert": false,
#   "fault_detected": false,
#   "anomaly_score": 0.15,
#   "fault_type": null,
#   "is_demand_spike": false
# }
```

### Step 5: Trigger an Alert

```bash
# Test with high voltage (fault condition)
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_data": {
      "voltage": 430.0,
      "current": 8.0,
      "temperature": 35.0,
      "timestamp": 1234567890,
      "inverter_id": "INV_001",
      "village_id": "KA_001"
    }
  }'

# Expected: Alert detected if anomaly_score > 0.75 and NOT a demand spike
```

---

## 📚 What's Implemented

| Component | File | Status |
|-----------|------|--------|
| **State Machine** | `src/grid_state.py` | ✅ Complete |
| **Fault Detector Agent** | `src/agents/fault_detector.py` | ✅ Complete |
| **Load Forecaster Agent** | `src/agents/load_forecaster.py` | ✅ Complete |
| **Alert Dispatcher Agent** | `src/agents/alert_dispatcher.py` | ✅ Complete |
| **A2A Protocol** | `src/a2a_protocol.py` | ✅ Complete |
| **Memory System** | `src/memory_store.py` | ✅ Complete |
| **Bedrock Integration** | `src/bedrock_integration.py` | ✅ Complete |
| **LangGraph Orchestrator** | `src/orchestrator.py` | ✅ Complete |
| **API Routes** | `src/api_routes.py` | ✅ Complete |
| **Integration Tests** | `test/test_vidyutseva.py` | ✅ 15+ tests |
| **Architecture Docs** | `VIDYUTSEVA_ARCHITECTURE.md` | ✅ Complete |
| **Deployment Guide** | `DEPLOYMENT_GUIDE.md` | ✅ Complete |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│            MQTT Sensor Data                         │
│  (voltage, current, temperature)                    │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────┐
    │     Fault Detector Agent           │
    │  (Isolation Forest Anomaly)        │
    │  Score: 0-1                        │
    │  Types: overvoltage, overtemp...   │
    └────┬─────────────────────────────┬─┘
         │                             │
         │ A2A Query                   │
         ▼                             │
    ┌─────────────────────────────┐    │
    │  Load Forecaster Agent      │    │
    │  (LSTM-like prediction)     │    │
    │  2h/4h demand forecast      │    │
    │  is_demand_spike?           │    │
    └────┬──────────────────┬─────┘    │
         │ A2A Response     │          │
         └────┬────────────┬┘          │
              │            └───────────┘
              │
              ▼
    ┌──────────────────────────────┐
    │  Alert Dispatcher Agent      │
    │  Consensus Logic             │
    │  (fault AND NOT spike AND    │
    │   high confidence)           │
    └────┬───────────────────────┬─┘
         │                       │
    NO   │                       │ YES
    ALERT│                       │ALERT
         │                       │
         │                ┌──────▼──────┐
         │                │  Bedrock    │
         │                │  Claude     │
         │                │  (Alert Gen)│
         │                └──────┬──────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
            Output Decision + Message
            (Kannada/Hindi alert)
```

---

## 🧪 Test Coverage

### Run All Tests
```bash
pytest test/test_vidyutseva.py -v
```

### Run Specific Test Class
```bash
pytest test/test_vidyutseva.py::TestFaultDetection -v
pytest test/test_vidyutseva.py::TestAlertDispatcher -v
pytest test/test_vidyutseva.py::TestA2AMessaging -v
```

### Test Categories
- ✅ **Fault Detection**: Normal data, overvoltage, overtemp
- ✅ **Load Forecasting**: Forecast generation, demand spikes
- ✅ **Alert Dispatch**: Consensus logic, alert generation
- ✅ **A2A Messaging**: Send/receive, deduplication
- ✅ **Memory**: Save/load persistence
- ✅ **Bedrock**: Fallback alert generation
- ✅ **End-to-End**: Complete pipeline flows

---

## 📖 Documentation

### Architecture Overview
Read: `VIDYUTSEVA_ARCHITECTURE.md`
- System design
- Agent workflows
- Memory system
- A2A protocol
- Bedrock integration

### Deployment Instructions
Read: `DEPLOYMENT_GUIDE.md`
- Local setup
- Docker deployment
- AWS CDK deployment
- RDS configuration
- Monitoring & logging
- Troubleshooting

---

## 🔧 Configuration

### Environment Variables

```bash
# AWS
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Local development
export LOCAL_DEV=1

# Bedrock model
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Telegram farmer alerts
export TELEGRAM_BOT_TOKEN=your_telegram_bot_token
export TELEGRAM_DEFAULT_CHAT_ID=default_farmer_or_group_chat_id

# Optional: route alerts by village or farmer ID
export TELEGRAM_CHAT_ID_KA_001=farmer_chat_id_for_village_KA_001
export TELEGRAM_CHAT_ID_FARMER_001=chat_id_for_farmer_001

# Optional MCP Gateway mode for the Alert Dispatcher tool call
export GATEWAY_URL=your_agentcore_gateway_streamable_http_url
export COGNITO_TOKEN_URL=your_cognito_token_url
export COGNITO_CLIENT_ID=your_cognito_client_id
export COGNITO_CLIENT_SECRET=your_cognito_client_secret
export COGNITO_SCOPE=your_gateway_scope
```

### Customization

**Adjust Fault Detection Threshold**:
```python
# In src/agents/fault_detector.py
ANOMALY_THRESHOLD = 0.6  # Default, range 0-1
```

**Adjust Alert Confidence**:
```python
# In src/agents/alert_dispatcher.py
ALERT_CONFIDENCE_THRESHOLD = 0.75  # Default, range 0-1
```

**Change Demand Spike Threshold**:
```python
# In src/agents/load_forecaster.py
is_demand_spike = demand_2h > current_demand * 1.2  # 20% increase threshold
```

---

## 🚢 Deployment Paths

### Option 1: Docker (Recommended for Local Testing)
```bash
docker build -t vidyutseva:latest .
docker run -e AWS_ACCESS_KEY_ID=xxx \
           -e AWS_SECRET_ACCESS_KEY=xxx \
           -p 8000:8000 vidyutseva:latest
```

### Option 2: AWS Lambda (Production)
```bash
cd cdk
npm install
npm run cdk:deploy
```

### Option 3: Docker Compose (Multi-Service)
```bash
docker-compose up -d
# Runs agent + PostgreSQL
```

---

## ⚙️ How Agents Work

### Fault Detector Flow
1. Receives sensor data (voltage, current, temperature)
2. Runs Isolation Forest anomaly detection
3. Scores anomaly 0-1 (0=normal, 1=extreme)
4. Classifies fault type (overvoltage, overtemp, etc.)
5. If score > 0.6, sends A2A query to Load Forecaster
6. Saves to memory

### Load Forecaster Flow
1. Receives A2A query from Fault Detector
2. Forecasts demand 2-4 hours ahead (LSTM-like)
3. Compares forecast vs current demand
4. Determines if it's a demand spike
5. Sends A2A response with confidence
6. Saves forecast to memory

### Alert Dispatcher Flow
1. Receives results from both agents
2. Applies consensus logic:
   - Alert if (fault AND NOT demand_spike AND confidence > 0.75)
   - Otherwise, NO ALERT
3. If alerting, calls Bedrock Claude for localized message
4. Saves alert decision to memory
5. Returns alert message in Kannada/Hindi

---

## 📊 Example Responses

### Normal Conditions
```json
{
  "should_alert": false,
  "fault_detected": false,
  "anomaly_score": 0.15,
  "fault_type": null,
  "is_demand_spike": false,
  "demand_forecast": {
    "demand_2h": 8.2,
    "demand_current": 8.0,
    "confidence": 0.85
  }
}
```

### Fault Detected (Overvoltage)
```json
{
  "should_alert": true,
  "alert_message": "ಇನ್ವರ್ಟರ್ ಓವರ್ವೋಲ್ಟೇಜ್. ಬುಧವಾರ ಪರಿವರ್ತನೆ ಮಾಡಿ. ₹2000 ಖರ್ಚು.",
  "fault_detected": true,
  "anomaly_score": 0.82,
  "fault_type": "inverter_overvoltage",
  "is_demand_spike": false
}
```

### False Alarm Prevention (Demand Spike)
```json
{
  "should_alert": false,
  "fault_detected": true,
  "anomaly_score": 0.71,
  "fault_type": "inverter_overvoltage",
  "is_demand_spike": true,
  "reason": "Anomaly coincides with forecasted demand spike. Likely NOT a fault."
}
```

---

## 🐛 Common Issues & Fixes

### Issue: "Module not found" when importing agents
**Fix**: Make sure you're in `/workspaces/Eliyonix/backend/echoRed` and run tests with `pytest`

### Issue: AWS credentials invalid
**Fix**: Run `aws configure` and enter your credentials, or export environment variables

### Issue: High latency (2+ seconds per request)
**Fix**: Bedrock calls can be slow; use fallback alerts or increase timeout

### Issue: Isolation Forest import error
**Fix**: `pip install scikit-learn numpy`

---

## 📞 Support

For issues:
1. Check CloudWatch logs: `aws logs tail /aws/lambda/vidyutseva-agent`
2. Review DEPLOYMENT_GUIDE.md troubleshooting section
3. Run test suite: `pytest test/test_vidyutseva.py -v`

---

## 🎯 Next Steps

1. ✅ Run tests: `pytest test/test_vidyutseva.py -v`
2. ✅ Start dev server: `agentcore dev`
3. ✅ Send test data: `curl ...`
4. ✅ Deploy to Docker: `docker build -t vidyutseva .`
5. ✅ Deploy to AWS: `cd cdk && npm run cdk:deploy`

---

**Happy building! 🚀 The VidyutSeva system is ready for production use.**
