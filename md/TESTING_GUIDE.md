# StormGuard Testing Guide

Complete testing guide for all components of the StormGuard AI platform.

## 🏃 Quick Start

### 1. Run the Full Test Suite

```bash
# Run all tests
python test_suite.py --full

# Run specific test category
python test_suite.py --api              # API endpoints only
python test_suite.py --database         # Database connectivity
python test_suite.py --airflow          # Airflow integration
python test_suite.py --verbose          # Show detailed output
```

### 2. Expected Output

```
[14:23:45] ℹ Starting StormGuard Integration Test Suite
[14:23:45] ℹ API URL: http://localhost:8000

============================================================
  API Tests
============================================================

[14:23:46] ✓ API Health Check: PASS (0.35s) - API is responding
[14:23:47] ✓ User Registration: PASS (0.45s) - User registered successfully
[14:23:48] ✓ User Login: PASS (0.32s) - Authentication successful
[14:23:49] ✓ User Profile: PASS (0.28s) - Profile retrieved
[14:23:50] ✓ Alert Send: PASS (0.41s) - Alerts sent successfully
[14:23:55] ✓ Chat Message: PASS (4.85s) - Message processed

============================================================
  Test Summary
============================================================

Results:
  Total:    12
  Passed:   12
  Failed:    0
  Duration: 6.66s
```

## 📋 Detailed Test Scenarios

### Phase 1: User Management Tests

#### Test 1.1: User Registration
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User",
    "phone": "+1234567890",
    "location": "New York, NY",
    "timezone": "America/New_York"
  }'
```

**Expected Response (201):**
```json
{
  "id": "uuid-here",
  "email": "testuser@example.com",
  "full_name": "Test User",
  "created_at": "2024-02-27T14:30:00Z",
  "updated_at": "2024-02-27T14:30:00Z"
}
```

#### Test 1.2: User Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@example.com&password=SecurePassword123!"
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### Test 1.3: Get User Profile
```bash
TOKEN="your-auth-token"
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

#### Test 1.4: Update Preferences
```bash
TOKEN="your-auth-token"
curl -X PUT http://localhost:8000/api/v1/users/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hurricane_alerts": true,
    "heat_wave_alerts": true,
    "flood_alerts": false,
    "min_risk_level": "MEDIUM",
    "alert_channels": ["push", "email"],
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
  }'
```

### Phase 2: Chat & RAG Tests

#### Test 2.1: Send Chat Message
```bash
TOKEN="your-auth-token"
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the safest places during a hurricane?"
  }'
```

**Expected Response:**
- Status: 200 OK
- Response contains AI answer with disaster preparedness information
- Sources should reference knowledge base

#### Test 2.2: Get Chat History
```bash
TOKEN="your-auth-token"
curl -X GET http://localhost:8000/api/v1/chat/history \
  -H "Authorization: Bearer $TOKEN"
```

#### Test 2.3: List Chat Sessions
```bash
TOKEN="your-auth-token"
curl -X GET http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer $TOKEN"
```

### Phase 3: Alert Tests

#### Test 3.1: Send Bulk Alerts
```bash
TOKEN="your-auth-token"
curl -X POST http://localhost:8000/api/v1/alerts/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["user-1", "user-2", "user-3"],
    "disaster_type": "hurricane",
    "title": "Hurricane Warning",
    "message": "Hurricane approaching your area",
    "risk_level": "HIGH",
    "risk_score": 0.85,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_km": 200
  }'
```

#### Test 3.2: Get User Alerts
```bash
TOKEN="your-auth-token"
curl -X GET http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN"
```

#### Test 3.3: Mark Alert as Read
```bash
TOKEN="your-auth-token"
curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/read \
  -H "Authorization: Bearer $TOKEN"
```

#### Test 3.4: Track Alert Click
```bash
TOKEN="your-auth-token"
curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/click \
  -H "Authorization: Bearer $TOKEN"
```

#### Test 3.5: Get Alert Statistics
```bash
TOKEN="your-auth-token"
curl -X GET http://localhost:8000/api/v1/alerts/stats \
  -H "Authorization: Bearer $TOKEN"
```

### Phase 4: Frontend Tests

#### Test 4.1: Load Chat Interface
```bash
# Open in browser
http://localhost:8000
```

**Verification:**
- ✓ Login modal appears
- ✓ Registration form works
- ✓ Chat interface loads after login
- ✓ Chat input field is responsive
- ✓ Messages appear in real-time

#### Test 4.2: WebSocket Connection
```bash
# Check browser console for WebSocket events
# Should see: Connection established
# On message: New message appears in UI instantly
```

#### Test 4.3: Real-time Alerts
```bash
# While logged in, alerts should appear in the alert panel
# Every 30 seconds, alerts refresh automatically
```

## 🧪 Integration Tests

### Test I1: Airflow to API Integration

**Setup:**
```bash
# 1. Insert test prediction
psql -d stormguard -c "
  INSERT INTO predictions (
    prediction_id, disaster_type, risk_score,
    latitude, longitude, affected_radius_km
  ) VALUES (
    gen_random_uuid(), 'hurricane', 0.85,
    40.7128, -74.0060, 200
  );
"

# 2. Trigger DAG
airflow dags trigger stormguard_alert_trigger

# 3. Monitor execution
airflow tasks logs stormguard_alert_trigger get_latest_predictions
airflow tasks logs stormguard_alert_trigger identify_affected_users
airflow tasks logs stormguard_alert_trigger send_alerts
```

**Verification:**
- ✓ DAG starts execution
- ✓ Predictions are fetched
- ✓ Affected users are identified
- ✓ Alerts are sent via API
- ✓ Metrics are recorded

### Test I2: End-to-End User Flow

```python
"""
Complete user journey test
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    # 1. Register user
    print("[1/5] Registering user...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": f"flow-test-{datetime.now().timestamp()}@test.com",
        "password": "TestPassword123!",
        "full_name": "Flow Test User",
        "location": "New York, NY",
        "timezone": "America/New_York"
    })
    assert resp.status_code in [200, 201, 409], f"Registration failed: {resp.status_code}"
    
    # 2. Login
    print("[2/5] Logging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
        "username": "flow-test@test.com",
        "password": "TestPassword123!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.status_code}"
    token = resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Update preferences
    print("[3/5] Updating preferences...")
    resp = requests.put(f"{BASE_URL}/api/v1/users/preferences", headers=headers, json={
        "hurricane_alerts": True,
        "min_risk_level": "MEDIUM"
    })
    assert resp.status_code == 200, f"Preferences update failed: {resp.status_code}"
    
    # 4. Send chat message
    print("[4/5] Sending chat message...")
    resp = requests.post(f"{BASE_URL}/api/v1/chat/message", headers=headers, json={
        "message": "What should I prepare for a hurricane?"
    })
    assert resp.status_code == 200, f"Chat failed: {resp.status_code}"
    
    # 5. Get alerts
    print("[5/5] Retrieving alerts...")
    resp = requests.get(f"{BASE_URL}/api/v1/alerts", headers=headers)
    assert resp.status_code == 200, f"Alerts retrieval failed: {resp.status_code}"
    
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_complete_flow()
```

## 📊 Performance Testing

### Load Test: Alert Sending

```python
"""
Test alert sending with multiple concurrent users
"""

import concurrent.futures
import requests
import time
from statistics import mean, stdev

def send_alert(user_id):
    """Send a single alert"""
    try:
        resp = requests.post(
            "http://localhost:8000/api/v1/alerts/send",
            headers={"Authorization": "Bearer your-token"},
            json={
                "user_ids": [f"user-{user_id}"],
                "disaster_type": "hurricane",
                "title": "Test",
                "message": "Test",
                "risk_level": "HIGH",
                "risk_score": 0.85,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "radius_km": 150
            },
            timeout=10
        )
        return resp.elapsed.total_seconds()
    except Exception as e:
        print(f"Error: {e}")
        return None

def load_test(num_users=100):
    """Run load test"""
    print(f"Running load test with {num_users} concurrent alerts...")
    
    start = time.time()
    times = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_alert, i) for i in range(num_users)]
        for future in concurrent.futures.as_completed(futures):
            t = future.result()
            if t is not None:
                times.append(t)
    
    duration = time.time() - start
    
    print(f"""
    Results:
    - Total time: {duration:.2f}s
    - Successful: {len(times)}/{num_users}
    - Average response time: {mean(times):.3f}s
    - Min response time: {min(times):.3f}s
    - Max response time: {max(times):.3f}s
    - Std deviation: {stdev(times) if len(times) > 1 else 0:.3f}s
    - Throughput: {len(times)/duration:.1f} alerts/second
    """)

if __name__ == "__main__":
    load_test(100)
```

## ✅ Testing Checklist

- [ ] API health check passes
- [ ] User registration works
- [ ] User login returns valid token
- [ ] User profile can be retrieved
- [ ] Preferences can be updated
- [ ] Chat messages are processed
- [ ] Chat history is retrievable
- [ ] Alerts can be sent
- [ ] Alerts appear in user's list
- [ ] Alert read/click tracking works
- [ ] Alert statistics are calculated
- [ ] Frontend chat UI loads
- [ ] WebSocket connection works
- [ ] Real-time messages appear
- [ ] Airflow DAG is registered
- [ ] Airflow variables are set
- [ ] Database tables exist
- [ ] Database connections work
- [ ] Docker containers are healthy
- [ ] All environment variables are set

## 🔍 Debugging Tips

### Check API Logs
```bash
# Stream API logs
docker logs -f stormguard-api

# View error logs
docker logs stormguard-api | grep ERROR
```

### Check Airflow Logs
```bash
# View scheduler logs
docker logs -f airflow-scheduler

# View webserver
docker logs -f airflow-webserver

# Check DAG parse errors
airflow dags show-dependencies stormguard_alert_trigger
```

### Check Database
```bash
# Connect to database
psql -U postgres -d stormguard

# Check tables
\dt

# Check alert metrics
SELECT * FROM alert_metrics ORDER BY created_at DESC LIMIT 10;

# Check recent predictions
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 5;
```

### Check Firebase
```bash
# Test Firebase connection
python -c "
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate('firebase-credentials.json')
firebase_admin.initialize_app(cred)

# Send test notification
message = messaging.Message(
    data={'test': 'true'},
    tokens=['test-token-here']
)
response = messaging.send_each(message)
print(f'Successfully sent {response.successful} messages')
"
```

## 📈 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time (p95) | < 500ms | - |
| Chat Message Processing | < 3s | - |
| Alert Sending Success Rate | > 99% | - |
| Airflow DAG Execution Time | < 5 min | - |
| Database Query Time (p95) | < 100ms | - |
| Firebase FCM Delivery Rate | > 95% | - |

---

**Version**: 1.0.0
**Last Updated**: 2024-02-27
