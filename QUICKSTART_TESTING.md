# 🚀 Quick Start: Run Your First Tests

This guide will get you testing StormGuard in 5 minutes.

## Prerequisites

```bash
# Ensure you have:
✓ Python 3.9+
✓ PostgreSQL running
✓ Redis running
✓ Airflow running (optional, for DAG tests)
✓ API running on http://localhost:8000
```

## Step 1: Install Dependencies

```bash
cd StormGuard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest requests sqlalchemy
```

## Step 2: Run the Automated Test Suite

```bash
# One command - tests everything
python test_suite.py --full

# Or test specific areas:
python test_suite.py --api              # Just API endpoints
python test_suite.py --database         # Just database
python test_suite.py --airflow          # Just Airflow integration
```

### What Gets Tested

```
✓ API Health Check
✓ User Registration
✓ User Login & Authentication
✓ User Profile Retrieval
✓ Alert Sending
✓ Chat Messages (RAG)
✓ Database Connection
✓ All Database Tables
✓ Airflow DAG Registration
✓ Airflow Variables
```

## Step 3: Check Test Results

```
============================================================
  Test Summary
============================================================

Results:
  Total:    10
  Passed:   10        ← All tests passed? ✓ Success!
  Failed:    0
  Duration: 24.5s
```

## Step 4: Detailed Testing (Manual)

### Test 4A: Chat Interface

1. Open browser: http://localhost:8000
2. Click "Register" → Create test account
3. Login with your credentials
4. Type in chat: "What should I do in a hurricane?"
5. ✓ Should get AI response with disaster preparedness info

### Test 4B: Alerts

```bash
# Send request to API
curl -X POST http://localhost:8000/api/v1/alerts/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["test-user"],
    "disaster_type": "hurricane",
    "title": "Test Alert",
    "message": "This is a test",
    "risk_level": "HIGH",
    "risk_score": 0.85,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_km": 150
  }'

# Check response
# Should see: {"sent": 1, "failed": 0}
```

### Test 4C: Airflow Integration

```bash
# Trigger the alert DAG manually
airflow dags trigger stormguard_alert_trigger

# Watch it run
airflow dags logs stormguard_alert_trigger

# Verify metrics were recorded
psql -d stormguard -c "SELECT * FROM alert_metrics LIMIT 5;"
```

## Step 5: View Results

### Success Indicators

✅ All tests passed
✅ Chat interface responds
✅ Alerts are sent and recorded
✅ Airflow DAG executes
✅ Database metrics are populated

### If Tests Fail

Check the [TESTING_GUIDE.md](TESTING_GUIDE.md) troubleshooting section:

```bash
# Check API is running
curl http://localhost:8000/api/v1/health

# Check database connection
psql -d stormguard -c "SELECT 1;"

# Check Airflow
airflow dags list | grep stormguard

# View logs
docker logs stormguard-api | tail -20
```

## 📊 What's Being Tested?

### Phase 1: User Management ✓
- Registration with email validation
- Login and JWT token generation
- Profile access and updates
- Preference management
- Role-based access control

### Phase 2: Chat & RAG ✓
- Message processing through LLM
- Vector database embedding
- Disaster knowledge retrieval
- Conversation history
- Source attribution

### Phase 3: Alerts & Notifications ✓
- Alert creation and sending
- Firebase FCM push notifications
- User preference filtering
- Alert engagement tracking (read/click)
- Risk-level management

### Phase 4: Frontend ✓
- Web interface load and interaction
- WebSocket real-time communication
- Session management
- Chat/alert UI rendering
- Responsive design

### Airflow Integration ✓
- DAG registration and execution
- Prediction fetching
- Geographic user filtering
- Bulk alert dispatch
- Metrics recording

## 🎯 Next Steps

After successful testing:

1. **Load Testing**: Run performance tests
   ```bash
   python test_suite.py --perf --users 100
   ```

2. **Production Deployment**: Configure for production
   ```bash
   # Update .env with production values
   cp .env.example .env
   vim .env
   
   # Deploy with Kubernetes
   kubectl apply -f kubernetes/
   ```

3. **Monitoring Setup**: Enable metrics collection
   ```bash
   # Prometheus and Grafana
   docker-compose up prometheus grafana
   ```

4. **Scale to Production**: Handle real data
   - Import disaster prediction models
   - Configure Firebase for push notifications
   - Setup email/SMS alerts
   - Enable analytics collection

## 📚 Full Documentation

For detailed testing procedures, see:
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Complete test scenarios
- [AIRFLOW_INTEGRATION.md](AIRFLOW_INTEGRATION.md) - Airflow setup and monitoring
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Architecture and API reference
- [README.md](README.md) - Project overview

## 💬 Common Issues

**Q: Tests timeout**
```
A: Check if API is running
   curl http://localhost:8000/api/v1/health
```

**Q: Database connection fails**
```
A: Verify PostgreSQL is running
   psql -h localhost -U postgres
```

**Q: Chat doesn't respond**
```
A: Check OpenAI API key is set
   echo $OPENAI_API_KEY
```

**Q: Airflow DAG not found**
```
A: Reload DAGs
   airflow dags list --reload
```

## ✨ Success Checklist

- [ ] All tests pass
- [ ] Chat interface works
- [ ] Alerts are sent
- [ ] Airflow DAG executes
- [ ] Database is populated
- [ ] Frontend loads without errors
- [ ] WebSocket connects
- [ ] Firebase sends notifications

---

**Ready to test? Run this now:**

```bash
python test_suite.py --full
```

🚀 **Your StormGuard AI platform is ready to use!**
