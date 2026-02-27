# Airflow Integration Guide

Complete guide for integrating StormGuard alerts with Airflow prediction pipeline.

## 🎯 Overview

The alert trigger DAG monitors disaster predictions from the inference pipeline and automatically sends notifications to at-risk users via Firebase FCM.

**Integration Flow:**
```
Airflow Inference (every 6h)
        ↓
  [Predictions stored]
        ↓
Airflow Alert Trigger (every 6h)
        ↓
  [Query predictions]
        ↓
  [Find affected users]
        ↓
  [Apply preferences filter]
        ↓
  StormGuard API
        ↓
  [Send alerts]
        ↓
  Firebase FCM
        ↓
  [User devices]
```

## 📋 Setup

### 1. Run Database Migrations

```bash
# Initialize alert metrics tables
psql -h localhost -U airflow -d airflow \
  -f data_pipeline/migrations/002_airflow_integration.sql

# Or using Python
python data_pipeline/init_db.py init
```

**Verify tables created:**
```sql
\dt alert_*
\dt predictions
\dv daily_alert_summary
```

### 2. Configure Airflow Variables

```bash
# Option A: Using setup script
cd StormGuard
python airflow/setup_variables.py

# Option B: Manual (Airflow UI)
# Navigate to Admin > Variables and add:
```

**Required Variables:**

| Variable | Value | Example |
|----------|-------|---------|
| `STORMGUARD_API_URL` | API base URL | `http://localhost:8000` |
| `STORMGUARD_API_KEY` | JWT bearer token | `eyJhbGc...` |
| `ALERT_RISK_THRESHOLD` | Min risk to alert | `0.60` |
| `FIREBASE_CREDENTIALS_PATH` | FCM cert path | `/app/firebase-credentials.json` |

**Via Airflow CLI:**
```bash
airflow variables set STORMGUARD_API_URL http://localhost:8000
airflow variables set STORMGUARD_API_KEY "your-api-key"
airflow variables set ALERT_RISK_THRESHOLD 0.60
airflow variables set FIREBASE_CREDENTIALS_PATH /app/firebase-credentials.json
```

**Via Python script:**
```python
from airflow.models import Variable

Variable.set("STORMGUARD_API_URL", "http://localhost:8000")
Variable.set("STORMGUARD_API_KEY", "your-token")
Variable.set("ALERT_RISK_THRESHOLD", "0.60")
```

### 3. Enable the DAG

```bash
# The DAG is enabled by default
# Verify in Airflow UI: http://localhost:8050

# Or check via CLI
airflow dags list | grep stormguard_alert_trigger

# Unpause if needed
airflow dags unpause stormguard_alert_trigger
```

## 🧪 Testing

### Test 1: Manual DAG Trigger

```bash
# Trigger the DAG manually
airflow dags trigger stormguard_alert_trigger

# Check execution
airflow tasks list stormguard_alert_trigger
airflow task-instances list --dag-id stormguard_alert_trigger
```

### Test 2: Dry Run a Single Task

```bash
# Test the prediction fetching task
airflow dags test stormguard_alert_trigger 2024-02-27

# Test specific task
airflow tasks test stormguard_alert_trigger \
  get_latest_predictions \
  2024-02-27
```

### Test 3: Insert Test Data

```sql
-- Insert test prediction
INSERT INTO predictions (
    prediction_id,
    disaster_type,
    risk_score,
    latitude,
    longitude,
    affected_radius_km,
    created_at
) VALUES (
    gen_random_uuid(),
    'hurricane',
    0.85,      -- HIGH risk
    40.7128,   -- NYC latitude
    -74.0060,  -- NYC longitude
    150,       -- 150 km radius
    NOW()
);

-- Verify insertion
SELECT * FROM predictions 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

### Test 4: API Connectivity

```bash
# Test if API is accessible
curl -X GET http://localhost:8000/api/v1/health

# Test alert endpoint
curl -X POST http://localhost:8000/api/v1/alerts/send \
  -H "Authorization: bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["test-user-id"],
    "disaster_type": "hurricane",
    "title": "Test Hurricane Alert",
    "message": "This is a test alert",
    "risk_level": "HIGH",
    "risk_score": 0.85,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_km": 150
  }'
```

### Test 5: Check Airflow Logs

```bash
# View DAG logs
airflow dags logs stormguard_alert_trigger

# View specific task logs
airflow tasks logs stormguard_alert_trigger get_latest_predictions

# Export logs
airflow dags export-logs stormguard_alert_trigger /tmp/logs

# Check database for metrics
SELECT * FROM alert_metrics 
ORDER BY created_at DESC 
LIMIT 10;
```

### Test 6: Full Integration Test

```python
"""
Full integration test script
Run this to verify end-to-end flow
"""

import requests
import json
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuration
API_URL = "http://localhost:8000"
DB_URL = "postgresql://airflow:airflow@postgres:5432/airflow"

def test_integration():
    """Test complete flow"""
    
    print("=" * 60)
    print("StormGuard Airflow Integration Test")
    print("=" * 60)
    
    # 1. Check API health
    print("\n1. Checking API health...")
    try:
        resp = requests.get(f"{API_URL}/api/v1/health")
        print(f"   ✓ API is {'✓ UP' if resp.status_code == 200 else '✗ DOWN'}")
    except Exception as e:
        print(f"   ✗ API error: {e}")
        return
    
    # 2. Check database connection
    print("\n2. Checking database connection...")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"   ✓ Database connected ({user_count} users)")
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return
    
    # 3. Insert test prediction
    print("\n3. Inserting test prediction...")
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO predictions (
                    prediction_id, disaster_type, risk_score,
                    latitude, longitude, affected_radius_km
                ) VALUES (
                    gen_random_uuid(), :type, :risk,
                    :lat, :lon, :radius
                )
            """)
            conn.execute(query, {
                "type": "hurricane",
                "risk": 0.85,
                "lat": 40.7128,
                "lon": -74.0060,
                "radius": 150
            })
            conn.commit()
            print("   ✓ Test prediction inserted")
    except Exception as e:
        print(f"   ✗ Insert error: {e}")
        return
    
    # 4. Trigger DAG
    print("\n4. Triggering alert DAG...")
    try:
        import subprocess
        result = subprocess.run([
            "airflow", "dags", "trigger",
            "stormguard_alert_trigger"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✓ DAG triggered successfully")
        else:
            print(f"   ✗ DAG trigger error: {result.stderr}")
    except Exception as e:
        print(f"   ✗ Trigger error: {e}")
    
    # 5. Check metrics
    print("\n5. Checking alert metrics...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT timestamp, total_sent, total_failed
                FROM alert_metrics
                ORDER BY created_at DESC
                LIMIT 5
            """))
            
            rows = result.fetchall()
            if rows:
                print("   Recent alerts:")
                for row in rows:
                    print(f"     - {row[0]}: {row[1]} sent, {row[2]} failed")
            else:
                print("   (No metrics yet - DAG may not have run)")
    except Exception as e:
        print(f"   ✗ Metrics error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_integration()
```

**Run the test:**
```bash
python test_integration.py
```

## 🔍 Monitoring

### View DAG Performance

```sql
-- Alert success rate over past 7 days
SELECT * FROM alert_success_rate;

-- Daily summary
SELECT * FROM daily_alert_summary;

-- Per-type breakdown
SELECT 
    disaster_type,
    SUM(alerts_sent) as total_sent,
    SUM(alerts_failed) as total_failed,
    ROUND(100.0 * SUM(alerts_sent) / 
        NULLIF(SUM(alerts_sent) + SUM(alerts_failed), 0), 2) as success_rate
FROM alert_metrics_by_type
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY disaster_type
ORDER BY total_sent DESC;
```

### Airflow Metrics

```bash
# Get task duration stats
airflow dags show-dependencies stormguard_alert_trigger

# View task tree
airflow tasks list --tree stormguard_alert_trigger

# Recent runs
airflow dags list-runs --dag-id stormguard_alert_trigger --limit 10
```

## 🐛 Troubleshooting

### Issue: DAG not appearing

```bash
# Verify DAG file syntax
python -m py_compile airflow/dags/alert_trigger_dag.py

# Check Airflow parse errors
airflow tasks list stormguard_alert_trigger

# Restart scheduler
docker-compose restart airflow-scheduler

# Clear DAG cache
rm -rf $AIRFLOW_HOME/dags/__pycache__
```

### Issue: API connection failed

```python
# Check from within DAG context
from airflow.models import Variable
import requests

api_url = Variable.get("STORMGUARD_API_URL")
print(f"Testing connection to {api_url}")

try:
    resp = requests.get(f"{api_url}/api/v1/health", timeout=5)
    print(f"Response: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
```

### Issue: No users affected

```sql
-- Check prediction data
SELECT * FROM predictions 
WHERE created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC;

-- Check user data
SELECT COUNT(*) FROM users 
WHERE notification_enabled = true
AND notification_token IS NOT NULL;

-- Check preferences
SELECT COUNT(*) FROM user_preferences
WHERE hurricane_alerts = true;
```

### Issue: Metrics not recorded

```sql
-- Check if table exists
\dt alert_metrics

-- Check for errors
SELECT * FROM alert_metrics WHERE errors IS NOT NULL;

-- Verify table structure
\d alert_metrics
```

## 📊 Performance Tuning

### Optimize Geographic Queries

For large datasets, use PostGIS:
```bash
pip install geoalchemy2
```

```python
# Use PostGIS instead of bounding box
from geoalchemy2 import func

query = session.query(User).filter(
    func.ST_DWithin(
        User.location,
        func.ST_Point(pred_lon, pred_lat),
        radius_km * 1000  # Convert to meters
    )
)
```

### Batch Size Optimization

Adjust batch alert sending:
```python
# In alert_trigger_dag.py
BATCH_SIZE = 100  # Send in batches of 100

# Process in chunks
for i in range(0, len(users), BATCH_SIZE):
    batch = users[i:i+BATCH_SIZE]
    # Send batch
```

### Connection Pooling

Configure PostgreSQL connection pooling in Docker Compose:
```yaml
services:
  postgres:
    environment:
      POSTGRES_INIT_ARGS: "-c max_connections=200"
```

## 📈 Next Steps

1. **Schedule Calibration**: Adjust risk thresholds based on false vs true positive rates
2. **A/B Testing**: Test different alert times and messages
3. **User Analytics**: Track alert engagement (read/click rates)
4. **ML Feedback Loop**: Feed alert feedback back into model training
5. **Multi-channel**: Add SMS/Email alerts alongside push notifications

---

**Last Updated**: 2025-02-27
**Version**: 1.0.0
