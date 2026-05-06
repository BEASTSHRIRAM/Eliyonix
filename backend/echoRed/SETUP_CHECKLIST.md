# AI Recommendation System - Setup Checklist

## 📋 Pre-Flight Checklist

Use this checklist to track your progress setting up the AI recommendation system.

---

## Phase 1: Qdrant Connection ⚠️ CRITICAL

### Option A: Local Qdrant (Recommended)
- [ ] Docker installed and running
- [ ] Run `docker-compose up -d` in `backend/echoRed/`
- [ ] Update `.env`: `QDRANT_URL=http://localhost:6333`
- [ ] Update `.env`: `QDRANT_API_KEY=` (leave empty)
- [ ] Run `python test_qdrant.py`
- [ ] See "✓ Connected to Qdrant successfully!"
- [ ] No "mock mode" warnings

### Option B: Cloud Qdrant
- [ ] Check firewall/VPN settings
- [ ] Try mobile hotspot
- [ ] Verify credentials in `.env`
- [ ] Run `python test_qdrant.py`
- [ ] See "✓ Connected to Qdrant successfully!"
- [ ] No connection errors (10054)

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Phase 2: Synthetic Data Generation

- [ ] Qdrant connection working (Phase 1 complete)
- [ ] Run `python generate_synthetic_data.py`
- [ ] See "✓ Generated 168 data points"
- [ ] See "✓ Stored 168 sensor readings"
- [ ] See "✓ Stored 8 fault events"
- [ ] No "mock mode" warnings
- [ ] Collections created in Qdrant

**Expected Output**:
```
✓ Generated 168 data points (7 days × 24 hours)
  Total readings: 168
  Fault events: 8
  Fault rate: 4.8%

✓ Stored 168 sensor readings in 'sensor_readings' collection
✓ Stored 8 fault events in 'fault_history' collection
```

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Phase 3: Backend Testing

- [ ] Run `python run_local.py`
- [ ] No Qdrant connection errors
- [ ] Fault detection working
- [ ] Alerts generated
- [ ] No "mock mode" messages

**Expected Output**:
```
✓ Execution ID: xxx
Fault Detected: True/False
Anomaly Score: 0.xx
```

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Phase 4: API Testing

### Test 1: Health Check
- [ ] Backend running on port 8080
- [ ] Run: `curl http://localhost:8080/health`
- [ ] Response: `{"status": "healthy"}`

### Test 2: AI Recommendations
- [ ] Run: `curl http://localhost:8080/recommendations/ai?village_id=KA_001`
- [ ] Response status: `"success"` (NOT "mock")
- [ ] Response has `data_points_analyzed: 168`
- [ ] Response has `recommendations` array
- [ ] Recommendations have priorities (high/medium/low)

**Expected Response**:
```json
{
  "status": "success",
  "village_id": "KA_001",
  "data_points_analyzed": 168,
  "analysis": {
    "fault_rate": 0.048,
    "efficiency_score": 92.3,
    ...
  },
  "recommendations": [
    {
      "priority": "high",
      "title": "Overheating Issues",
      ...
    }
  ]
}
```

### Test 3: Component Recommendations
- [ ] Run: `curl http://localhost:8080/recommendations/solar`
- [ ] Run: `curl http://localhost:8080/recommendations/fault`
- [ ] Both return valid recommendations

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Phase 5: Frontend Integration

### Setup
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend running on port 8080
- [ ] Run: `cd frontend && npm run dev`
- [ ] Open: http://localhost:5173

### Testing
- [ ] Dashboard loads without errors
- [ ] See 4 stat cards (Solar, Fault, Forecast, Alerts)
- [ ] Each card has "Recommendation" button
- [ ] Click "Recommendation" on Solar Output card
- [ ] Modal opens with AI recommendations
- [ ] Recommendations show real data (not mock)
- [ ] See analysis period: "7 days"
- [ ] See data points: "168"
- [ ] Recommendations have priorities
- [ ] Close modal works

### Verify All Components
- [ ] Solar Output recommendation works
- [ ] Fault Score recommendation works
- [ ] Load Forecast recommendation works
- [ ] Active Alerts recommendation works

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Phase 6: Embeddings Verification

- [ ] Run `python test_embeddings.py`
- [ ] See "✓ Embedding structure correct (8 dimensions)"
- [ ] See "✓ Cyclic time encoding working"
- [ ] See "✓ Similar readings have high similarity"
- [ ] Cosine similarity scores > 0.8 for similar readings

**Expected Output**:
```
Testing embedding generation...
✓ Embedding structure: [v, i, t, ldr, h_sin, h_cos, d_sin, d_cos]
✓ Dimensions: 8
✓ Cyclic encoding: 23:00 close to 00:00 (similarity: 0.95)
```

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Phase 7: Real Hardware Integration (Optional)

### ESP32 Setup
- [ ] ESP32 connected to WiFi
- [ ] Sensors wired (voltage, current, temp, LDR)
- [ ] MQTT client configured
- [ ] Publishing to topic: `village/KA_001/sensors`

### Raspberry Pi Setup
- [ ] Raspberry Pi on same WiFi
- [ ] MQTT broker running (Mosquitto)
- [ ] MQTT subscriber script running
- [ ] Forwarding data to backend

### Backend Integration
- [ ] Backend receiving real sensor data
- [ ] Data stored in Qdrant
- [ ] Agents processing in real-time
- [ ] Recommendations updating based on real data

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Final Verification

### System Health
- [ ] Qdrant connection stable
- [ ] Backend running without errors
- [ ] Frontend accessible
- [ ] API endpoints responding
- [ ] No "mock mode" warnings anywhere

### Data Quality
- [ ] 168+ data points in Qdrant
- [ ] Embeddings are 8-dimensional
- [ ] Fault events recorded
- [ ] Historical data retrievable

### Functionality
- [ ] Recommendations generated successfully
- [ ] Priorities assigned correctly
- [ ] Confidence scores present
- [ ] Actions are actionable
- [ ] Frontend displays recommendations

### Performance
- [ ] API response time < 500ms
- [ ] Frontend loads quickly
- [ ] No lag when clicking buttons
- [ ] Modal opens smoothly

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## Troubleshooting Guide

### Issue: "Mock mode" warnings
**Symptom**: Logs show "Using mock mode" or "Qdrant not connected"  
**Solution**: Fix Qdrant connection (Phase 1)  
**Verify**: Run `python test_qdrant.py` → should pass

### Issue: "No historical data available"
**Symptom**: API returns empty recommendations  
**Solution**: Generate synthetic data (Phase 2)  
**Verify**: Check Qdrant collections have 168 points

### Issue: "Connection refused" on API calls
**Symptom**: `curl` commands fail with connection error  
**Solution**: Start backend with `python run_local.py`  
**Verify**: `curl http://localhost:8080/health` → returns healthy

### Issue: Frontend shows "Loading..." forever
**Symptom**: Recommendation modal stuck loading  
**Solution**: Check browser console for errors, verify backend is running  
**Verify**: Open DevTools → Network tab → check API calls

### Issue: Low confidence scores
**Symptom**: Recommendations have confidence < 0.5  
**Solution**: Need more historical data  
**Verify**: Run system longer or generate more synthetic data

### Issue: Empty recommendations array
**Symptom**: API returns `recommendations: []`  
**Solution**: System is healthy! No issues detected  
**Verify**: This is actually good - means no faults found

---

## Success Criteria

You've successfully set up the AI recommendation system when:

✅ **Qdrant**: Connected and storing data  
✅ **Backend**: Running without errors  
✅ **API**: Returns real recommendations (not mock)  
✅ **Frontend**: Displays recommendations in modal  
✅ **Data**: 168+ points with 8D embeddings  
✅ **Analysis**: Shows fault rates, trends, efficiency  
✅ **Recommendations**: Prioritized with confidence scores  

---

## Next Steps After Setup

1. **Monitor System**: Watch recommendations update as new data arrives
2. **Connect Hardware**: Integrate ESP32 → Raspberry Pi → Backend
3. **Tune Thresholds**: Adjust fault detection sensitivity
4. **Add Features**: Custom recommendation rules
5. **Scale Up**: Add more villages, more sensors
6. **Production Deploy**: AWS, Docker, CI/CD

---

## Quick Commands Reference

```bash
# Test Qdrant connection
python test_qdrant.py

# Generate synthetic data
python generate_synthetic_data.py

# Test embeddings
python test_embeddings.py

# Run backend
python run_local.py

# Test API
curl http://localhost:8080/health
curl http://localhost:8080/recommendations/ai?village_id=KA_001

# Run frontend
cd frontend && npm run dev

# Start local Qdrant
docker-compose up -d

# Stop local Qdrant
docker-compose down
```

---

## Documentation Reference

- **Quick Start**: `QUICKSTART_RECOMMENDATIONS.md`
- **Complete Guide**: `AI_RECOMMENDATION_GUIDE.md`
- **Data Flow**: `RECOMMENDATION_FLOW.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **This Checklist**: `SETUP_CHECKLIST.md`

---

## Progress Tracker

**Overall Progress**: ⬜⬜⬜⬜⬜⬜⬜ 0/7 phases complete

Update this as you complete each phase:
- Phase 1 (Qdrant): ⬜
- Phase 2 (Data): ⬜
- Phase 3 (Backend): ⬜
- Phase 4 (API): ⬜
- Phase 5 (Frontend): ⬜
- Phase 6 (Embeddings): ⬜
- Phase 7 (Hardware): ⬜

---

**Current Status**: 🔴 Blocked by Qdrant Connection

**Next Action**: Complete Phase 1 - Fix Qdrant connection

**Estimated Time**: 
- Phase 1: 15 minutes
- Phase 2: 5 minutes
- Phase 3-6: 10 minutes
- Total: ~30 minutes to full system

---

Good luck! 🚀
