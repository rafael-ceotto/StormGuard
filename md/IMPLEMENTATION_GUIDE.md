# StormGuard Phase 1-4 Implementation Guide

Complete guide for setting up and running all phases of the StormGuard intelligent agent platform.

## 🎯 Overview

StormGuard is a production-ready AI-powered disaster prediction platform with:

- **Phase 1**: User Management (Registration, Authentication, Preferences)
- **Phase 2**: RAG + Chat Integration (Historical Context, AI Responses)
- **Phase 3**: Push Notifications (Firebase FCM, Alert Management)
- **Phase 4**: Frontend Chat UI (WebSocket, Real-time Communication)

## 📋 Prerequisites

### System Requirements
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional, for containerized setup)

### API Keys Required
- **OpenAI** (Phase 2): `sk-...` key for GPT-3.5/GPT-4
- **Pinecone** (Phase 2): API key + environment for vector database
- **Firebase** (Phase 3): Service account JSON for push notifications

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Required variables:**
```dotenv
DATABASE_URL=postgresql://airflow:airflow@postgres:5432/airflow
JWT_SECRET_KEY=your-32-char-minimum-secret-key-here
OPENAI_API_KEY=sk-your-key
PINECONE_API_KEY=your-key
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
```

### 2. Database Initialization

```bash
# Option A: Using Python SQLAlchemy
python data_pipeline/init_db.py init

# Option B: Using SQL directly
psql -h localhost -U airflow -d airflow \
  -f data_pipeline/migrations/001_phase1_user_management.sql
```

**Verify tables created:**
```sql
psql -h localhost -U airflow -d airflow

\dt  -- List tables
\d users  -- Describe users table
```

### 3. Install Dependencies

```bash
# Create virtual environment (if needed)
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install all requirements
pip install -r requirements.txt

# Verify key packages
pip show langchain openai pinecone-client firebase-admin
```

### 4. Start API Server

```bash
# Navigate to project root
cd /path/to/StormGuard

# Run FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# API docs available at:
# http://localhost:8000/docs
# http://localhost:8000/redoc
```

### 5. Access the Chat Interface

Open in browser:
```
http://localhost:8000/chat
```

## 📚 API Endpoints Reference

### Authentication (Phase 1)

```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "city": "New York",
    "timezone": "America/New_York",
    "interests": ["hurricane", "heat_wave", "flood"]
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### User Management (Phase 1)

```bash
# Get user profile
curl -H "Authorization: bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/{user_id}

# Update profile
curl -X PUT http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city": "Los Angeles", "timezone": "America/Los_Angeles"}'

# Get preferences
curl -H "Authorization: bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/{user_id}/preferences

# Update preferences
curl -X PUT http://localhost:8000/api/v1/users/{user_id}/preferences \
  -H "Authorization: bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hurricane_alerts": true,
    "min_risk_level": "MEDIUM",
    "alert_radius_km": 150,
    "enable_push": true
  }'
```

### Chat & RAG (Phase 2)

```bash
# Send chat message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the hurricane risks in New York?",
    "session_id": "optional-session-uuid"
  }'

# Get chat history
curl -H "Authorization: bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/chat/history/{session_id}

# List chat sessions
curl -H "Authorization: bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/chat/sessions
```

### Alerts & Notifications (Phase 3)

```bash
# Get user alerts
curl -H "Authorization: bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/alerts/user/{user_id}

# Send alert to users (requires admin/backend trigger)
curl -X POST http://localhost:8000/api/v1/alerts/send \
  -H "Authorization: bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["user1", "user2"],
    "disaster_type": "hurricane",
    "title": "Hurricane Alert",
    "message": "Category 4 hurricane approaching",
    "risk_level": "CRITICAL",
    "risk_score": 0.95,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_km": 200
  }'

# Mark alert as read
curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/read \
  -H "Authorization: bearer YOUR_TOKEN"

# Get alert statistics
curl -H "Authorization: bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/alerts/stats/{user_id}
```

## 🔌 WebSocket Chat (Phase 4)

### Connect to WebSocket

```javascript
// JavaScript example
const token = localStorage.getItem('access_token');
const userId = localStorage.getItem('user_id');
const sessionId = 'unique-session-id';

const ws = new WebSocket(
  `ws://localhost:8000/api/v1/chat/ws/${userId}/${sessionId}`
);

ws.onopen = () => {
  console.log('Connected');
  // Send message
  ws.send(JSON.stringify({ message: "Tell me about flood risks" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data.response);
  console.log('Sources:', data.sources);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

## 🏗️ Project Structure

```
StormGuard/
├── api/
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI application
│   ├── routers/
│   │   ├── auth.py            # Phase 1: Authentication
│   │   ├── users.py           # Phase 1: User management
│   │   ├── chat.py            # Phase 2/4: Chat endpoints
│   │   ├── alerts.py          # Phase 3: Alert management
│   │   ├── predictions.py     # Existing: ML predictions
│   │   └── health.py          # Health checks
│   ├── services/
│   │   ├── rag_service.py     # Phase 2: RAG implementation
│   │   └── notification_service.py  # Phase 3: Firebase FCM
│   ├── schemas/
│   │   └── user.py            # Phase 1: Pydantic validation
│   └── utils/
│       ├── auth.py            # JWT utilities
│       ├── db.py              # Database session
│       └── __init__.py
├── app/
│   ├── templates/
│   │   └── chat.html          # Phase 4: Chat UI
│   └── static/
│       ├── css/
│       │   └── chat.css       # Chat styles
│       └── js/
│           └── chat.js        # Chat logic
├── data_pipeline/
│   ├── db_models.py           # Phase 1: SQLAlchemy models
│   ├── init_db.py             # Database initialization
│   └── migrations/
│       └── 001_phase1_user_management.sql
├── requirements.txt            # All dependencies
├── .env.example                # Environment template
└── docker-compose.yml          # Container orchestration
```

## 🧪 Testing

### Run Unit Tests

```bash
# Phase 1 tests
pytest tests/test_phase1_user_management.py -v

# Run specific test
pytest tests/test_phase1_user_management.py::TestRegistration::test_register_user_success -v

# Run with coverage
pytest --cov=api tests/
```

### Manual Testing

```bash
# Register user
python -c "
import requests
resp = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'email': 'test@example.com',
    'full_name': 'Test User',
    'latitude': 40.7128,
    'longitude': -74.0060,
    'timezone': 'UTC'
})
print(resp.json())
"

# Save token for later requests
export TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' | jq -r '.access_token')

# Test protected endpoint
curl -H "Authorization: bearer $TOKEN" \
  http://localhost:8000/api/v1/users/USER_ID
```

## 🔧 Configuration Deep Dive

### Phase 1: User Management Config

```python
# api/config.py
DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
JWT_SECRET_KEY = "your-secret-key-min-32-chars"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
```

### Phase 2: RAG Config

```python
# Required OpenAI credentials
OPENAI_API_KEY = "sk-..."

# Pinecone vector database
PINECONE_API_KEY = "pcak_..."
PINECONE_ENVIRONMENT = "production"
PINECONE_INDEX_NAME = "stormguard-rag"
```

### Phase 3: Firebase Config

```python
# Firebase service account JSON
FIREBASE_CREDENTIALS_PATH = "/path/to/firebase-credentials.json"

# Generate from Firebase Console:
# 1. Go to Project Settings
# 2. Click "Service Accounts" tab
# 3. Generate new private key
# 4. Save as firebase-credentials.json
```

## 📊 Database Schema

### Users Table
```sql
SELECT * FROM users;
-- Columns: id, email, full_name, latitude, longitude, 
--          city, country, timezone, interests, 
--          notification_enabled, notification_token,
--          created_at, updated_at, last_login
```

### User Preferences Table
```sql
SELECT * FROM user_preferences;
-- Columns: user_id, hurricane_alerts, heat_wave_alerts, 
--          flood_alerts, severe_storm_alerts,
--          min_risk_level, alert_radius_km, max_daily_alerts,
--          quiet_hours_start, quiet_hours_end,
--          enable_push, enable_email, enable_sms, updated_at
```

### Alerts Table
```sql
SELECT * FROM alerts;
-- Columns: id, user_id, disaster_type, title, message,
--          risk_level, risk_score, latitude, longitude, radius_km,
--          sent, read, clicked, created_at, sent_at, read_at
```

### Chat Messages Table
```sql
SELECT * FROM chat_messages;
-- Columns: id, user_id, user_message, assistant_response,
--          sources, session_id, tokens_used, created_at
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down

# Reset database
docker-compose exec postgres psql -U airflow -d airflow -c "DROP SCHEMA public CASCADE;"
docker-compose up postgres
```

### Manual Docker Build

```bash
# Build image
docker build -f Dockerfile.api -t stormguard-api:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://airflow:airflow@postgres:5432/airflow" \
  -e OPENAI_API_KEY="sk-..." \
  stormguard-api:latest
```

## ⚠️ Common Issues & Solutions

### Issue: "No such table: users"
**Solution**: Run database initialization
```bash
python data_pipeline/init_db.py init
```

### Issue: "Pinecone not initialized"
**Solution**: Pinecone is optional in Phase 2. Check:
- PINECONE_API_KEY is set in .env
- Pinecone index exists with specified name
- For development, RAG will work in degraded mode

### Issue: "Firebase credentials not found"
**Solution**: Firebase is optional in Phase 3. Check:
- FIREBASE_CREDENTIALS_PATH points to valid JSON file
- Or skip Firebase for Phase 1-2 testing

### Issue: "JWT validation failed"
**Solution**: Check JWT token:
- Token is include in Authorization header as: `bearer TOKEN`
- Token not expired (default: 24 hours)
- JWT_SECRET_KEY matches between generation and validation

### Issue: "WebSocket connection refused"
**Solution**: 
- Ensure API server is running on correct port
- Check browser console for error details
- Fallback to HTTP POST if WebSocket unavailable

## 📈 Performance Optimization

### Database Optimization
```sql
-- Check indexes
SELECT * FROM pg_indexes WHERE tablename = 'alerts';

-- Create additional indexes if needed
CREATE INDEX idx_alerts_risk_score ON alerts(risk_score DESC);
CREATE INDEX idx_users_location ON users USING gist(ll_to_earth(latitude, longitude));
```

### Caching Strategy
```python
# Use Redis for session storage
from redis import Redis
redis_client = Redis(host='localhost', port=6379, decode_responses=True)

# Cache frequently accessed data
cache_key = f"user_preferences:{user_id}"
redis_client.setex(cache_key, 3600, json.dumps(preferences))
```

### Load Testing
```bash
# Install locust
pip install locust

# Create locustfile.py and run
locust -f locustfile.py --host=http://localhost:8000

# Or use Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/health
```

## 🚀 Production Deployment

### Pre-deployment Checklist

- [ ] Change JWT_SECRET_KEY to production value
- [ ] Set API_DEBUG=False
- [ ] Configure proper database backups
- [ ] Set up monitoring and logging
- [ ] Configure CORS properly
- [ ] Enable HTTPS/SSL
- [ ] Set up database read replicas
- [ ] Configure Redis for session persistence
- [ ] Set up Firebase production credentials
- [ ] Test all endpoints with production data

### Example Production .env

```dotenv
# Production settings
API_DEBUG=False
API_WORKERS=8
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://prod_user:strong_password@prod-db.example.com:5432/stormguard_prod

# JWT
JWT_SECRET_KEY=generate-with-secrets.token_urlsafe(32)
JWT_EXPIRATION_HOURS=24

# OpenAI Production
OPENAI_API_KEY=sk-prod-key

# Pinecone Production
PINECONE_API_KEY=prod-key
PINECONE_ENVIRONMENT=production

# Firebase Production
FIREBASE_CREDENTIALS_PATH=/app/secrets/firebase-prod.json

# Logging
LOG_LEVEL=WARNING

# Redis
REDIS_URL=redis://prod-redis.example.com:6379/0
```

## 📝 Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Database Migrations**: docs/database_schema.md
- **Architecture**: docs/architecture.md
- **Contributing**: CONTRIBUTING.md

## 🤝 Contributing

1. Create feature branch
2. Make changes with proper testing
3. Regular commits (not large monolithic commits)
4. Create pull request with description
5. Wait for review and CI/CD to pass

## 📞 Support

For issues or questions:
1. Check GitHub issues
2. Review documentation
3. Test with minimal reproduction case
4. Open new issue with details

## 📄 License

MIT License - See LICENSE file

---

**Version**: 1.0.0 (Phase 1-4 Complete)
**Last Updated**: 2025-02-27
**Status**: Production Ready
