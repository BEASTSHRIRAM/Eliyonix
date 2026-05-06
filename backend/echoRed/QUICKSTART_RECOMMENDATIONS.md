# Quick Start: AI Recommendations

## 🚀 Get Started in 3 Steps

### Step 1: Fix Qdrant Connection ⚠️ CRITICAL

**Current Problem**: Network/firewall blocking Qdrant Cloud

**Quick Fix** (choose one):

#### Option A: Use Local Qdrant (Easiest)
```bash
# Start local Qdrant
docker-compose up -d

# Update .env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Test connection
python test_qdrant.py
```

#### Option B: Fix Cloud Connection
- Try mobile hotspot
- Disable VPN/firewall
- Check https://cloud.qdrant.io/

---

### Step 2: Generate 7 Days of Data

```bash
python generate_synthetic_data.py
```

**What it does**:
- Creates 168 hourly readings (7 days)
- Realistic solar patterns (day/night)
- Weather variations (sunny/cloudy/rainy)
- Random faults (5% rate)
- Stores in Qdrant with 8D embeddings

**Expected output**:
```
✓ Generated 168 data points
✓ Stored 168 sensor readings
✓ Stored 8 fault events
```

---

### Step 3: Test Recommendations

```bash
# Start backend
python run_local.py

# In another terminal, test API
curl http://localhost:8080/recommendations/ai?village_id=KA_001
```

**Expected response**:
```json
{
  "status": "success",
  "recommendations": [
    {
      "priority": "high",
      "title": "Overheating Issues",
      "action": "Check ventilation, clean cooling fans",
      "confidence": 0.90
    }
  ]
}
```

---

## ✅ Verification Checklist

- [ ] Qdrant connection working (no "mock mode" message)
- [ ] 168 data points stored in Qdrant
- [ ] Backend running on port 8080
- [ ] API returns recommendations (not mock data)
- [ ] Frontend shows recommendation buttons

---

## 🎯 What You Get

### AI analyzes 7 days of data and provides:

1. **Fault Rate Analysis**: How often faults occur
2. **Performance Trends**: Improving/declining/stable
3. **Fault Patterns**: Which types of faults are common
4. **Time-Based Insights**: Day vs night issues
5. **Weather Impact**: Rainy days, cloudy days
6. **Efficiency Scores**: Overall system health (0-100)

### Recommendations include:

- **Priority**: High/Medium/Low
- **Category**: Maintenance, cooling, electrical, etc.
- **Title**: Clear problem statement
- **Description**: What's happening
- **Action**: What to do about it
- **Confidence**: How certain the AI is (0-1)
- **Impact**: Why it matters

---

## 🔧 Troubleshooting

### "Mock mode - Data not stored"
→ Fix Qdrant connection (Step 1)

### "No historical data available"
→ Run synthetic data generator (Step 2)

### "Connection refused"
→ Start backend: `python run_local.py`

### "Empty recommendations"
→ Need more data or check Qdrant collections

---

## 📊 Frontend Integration

The frontend already has everything ready:

1. **Dashboard Cards**: Each has a "Recommendation" button
2. **Modal**: Shows detailed AI recommendations
3. **History**: View past recommendations
4. **Auto-refresh**: Updates every 30 seconds

Just start the frontend:
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 and click any "Recommendation" button!

---

## 🎓 How It Works

```
ESP32 Sensors → MQTT → Backend Agents → Qdrant Vector DB
                                              ↓
                                    8D Embeddings
                                    [v, i, t, ldr, hour_sin, hour_cos, dow_sin, dow_cos]
                                              ↓
                                    Semantic Search
                                              ↓
                                    AI Analysis (7 days)
                                              ↓
                                    Prioritized Recommendations
                                              ↓
                                    Frontend Dashboard
```

---

## 📝 Example Recommendation

```json
{
  "priority": "high",
  "category": "cooling",
  "title": "Overheating Issues",
  "description": "Inverter overheating detected 3 times in past 7 days.",
  "action": "Check ventilation, clean cooling fans, verify ambient temperature",
  "confidence": 0.90,
  "impact": "High - reduces lifespan and efficiency"
}
```

---

## 🚀 Ready?

1. Fix Qdrant → 2. Generate data → 3. Test API → 4. View in frontend

**Need help?** Check `AI_RECOMMENDATION_GUIDE.md` for detailed documentation.
