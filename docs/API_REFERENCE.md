# 📚 StormGuard AI - API Reference

## Base URL
```
http://localhost:8000  (Development)
https://api.stormguard.ai  (Production)
```

## Authentication
Currently uses no authentication (development mode).

In production, set Authorization header:
```
Authorization: Bearer {api_key}
```

---

## Endpoints

### Health & Status

#### GET /health
Basic health check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-26T15:30:45.123456",
  "service": "StormGuard API",
  "version": "1.0.0"
}
```

---

#### GET /ready
Kubernetes readiness probe
```bash
curl http://localhost:8000/ready
```

#### GET /live
Kubernetes liveness probe
```bash
curl http://localhost:8000/live
```

---

### Predictions

#### POST /api/v1/predict
Get disaster probability for a location

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d {
    "latitude": 25.7617,
    "longitude": -80.1918,
    "temperature": 28.5,
    "humidity": 75,
    "pressure": 1010.25,
    "wind_speed": 12.5,
    "wind_direction": 200,
    "precipitation": 0.5
  }
```

**Parameters:**
| Field | Type | Range | Required | Description |
|-------|------|-------|----------|-------------|
| latitude | float | [-90, 90] | Yes | Geographic latitude |
| longitude | float | [-180, 180] | Yes | Geographic longitude |
| temperature | float | [-50, 60] | Yes | Temperature (°C) |
| humidity | float | [0, 100] | Yes | Relative humidity (%) |
| pressure | float | [870, 1060] | Yes | Atmospheric pressure (hPa) |
| wind_speed | float | [0, 100] | Yes | Wind speed (km/h) |
| wind_direction | int | [0, 360] | Yes | Wind direction (degrees) |
| precipitation | float | [0, ∞] | No | Precipitation (mm) |

**Response:**
```json
{
  "disaster_type": "flood",
  "probability": 0.35,
  "risk_level": "MEDIUM",
  "confidence_interval_lower": 0.30,
  "confidence_interval_upper": 0.40,
  "lead_time_hours": 48,
  "location": {
    "latitude": 25.7617,
    "longitude": -80.1918
  },
  "prediction_time": "2024-02-26T15:30:45.123456"
}
```

**Risk Levels:**
- `LOW`: Probability < 0.2
- `MEDIUM`: Probability 0.2-0.5
- `HIGH`: Probability 0.5-0.8
- `CRITICAL`: Probability > 0.8

**Disaster Types:**
- `hurricane`
- `flood`
- `heat_wave`
- `severe_storm`

---

#### POST /api/v1/predict_batch
Batch predictions for multiple locations

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict_batch" \
  -H "Content-Type: application/json" \
  -d {
    "locations": [
      {
        "latitude": 25.7617,
        "longitude": -80.1918,
        "temperature": 28.5,
        "humidity": 75,
        "pressure": 1010.25,
        "wind_speed": 12.5,
        "wind_direction": 200
      },
      {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "temperature": 15.2,
        "humidity": 65,
        "pressure": 1013.2,
        "wind_speed": 14.2,
        "wind_direction": 220
      }
    ]
  }
```

**Response:**
```json
{
  "predictions": [
    {
      "disaster_type": "flood",
      "probability": 0.35,
      "risk_level": "MEDIUM",
      ...
    },
    {
      "disaster_type": "severe_storm",
      "probability": 0.62,
      "risk_level": "HIGH",
      ...
    }
  ],
  "count": 2,
  "timestamp": "2024-02-26T15:30:45.123456"
}
```

---

#### GET /api/v1/predictions/{location_id}
Get prediction history for a location

**Request:**
```bash
curl "http://localhost:8000/api/v1/predictions/miami_florida?days=7"
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | int | 7 | Number of days of history |

**Response:**
```json
{
  "location_id": "miami_florida",
  "predictions": [
    {
      "timestamp": "2024-02-26T15:30:45",
      "probability": 0.35,
      "risk_level": "MEDIUM"
    }
  ],
  "days": 7
}
```

---

### Models

#### GET /api/v1/models
List available models

**Request:**
```bash
curl http://localhost:8000/api/v1/models
```

**Response:**
```json
{
  "models": [
    {
      "name": "cnn_lstm_v1",
      "type": "CNN-LSTM",
      "status": "production",
      "auc": 0.92,
      "created": "2024-01-15"
    },
    {
      "name": "transformer_v1",
      "type": "Temporal Fusion Transformer",
      "status": "staging",
      "auc": 0.94,
      "created": "2024-02-10"
    }
  ],
  "timestamp": "2024-02-26T15:30:45"
}
```

---

#### GET /api/v1/models/{model_name}
Get model metadata

**Request:**
```bash
curl http://localhost:8000/api/v1/models/cnn_lstm_v1
```

**Response:**
```json
{
  "name": "cnn_lstm_v1",
  "version": "1.0",
  "status": "production",
  "metrics": {
    "auc": 0.92,
    "pr_auc": 0.88,
    "brier_score": 0.15
  },
  "training_date": "2024-01-15"
}
```

---

#### POST /api/v1/models/{model_name}/promote
Promote model to different stage

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/models/transformer_v1/promote" \
  -H "Content-Type: application/json" \
  -d '{"target_stage": "production"}'
```

**Response:**
```json
{
  "model": "transformer_v1",
  "previous_stage": "staging",
  "new_stage": "production",
  "timestamp": "2024-02-26T15:30:45"
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 500 | Internal server error |
| 503 | Service unavailable |

### Common Errors
```json
// Invalid coordinates
{
  "detail": "Latitude must be between -90 and 90"
}

// Missing required field
{
  "detail": "Field 'temperature' is required"
}

// Model not found
{
  "detail": "Model 'unknown_model' not found"
}
```

---

## Rate Limiting

Currently no rate limits in development mode.

In production:
- **Single predictions:** 100 requests/minute
- **Batch predictions:** 10 requests/minute (max 1000 locations/batch)

---

## Caching

The API uses Redis for caching:
- Predictions cached for **6 hours**
- Models cached for **24 hours**
- Health checks cached for **1 minute**

---

## Examples

### Python
```python
import requests

url = "http://localhost:8000/api/v1/predict"

data = {
    "latitude": 25.7617,
    "longitude": -80.1918,
    "temperature": 28.5,
    "humidity": 75,
    "pressure": 1010.25,
    "wind_speed": 12.5,
    "wind_direction": 200,
    "precipitation": 0.5
}

response = requests.post(url, json=data)
prediction = response.json()

print(f"Risk Level: {prediction['risk_level']}")
print(f"Probability: {prediction['probability']:.2%}")
```

### JavaScript
```javascript
const data = {
    latitude: 25.7617,
    longitude: -80.1918,
    temperature: 28.5,
    humidity: 75,
    pressure: 1010.25,
    wind_speed: 12.5,
    wind_direction: 200,
    precipitation: 0.5
};

fetch('http://localhost:8000/api/v1/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
})
.then(r => r.json())
.then(prediction => {
    console.log(`Risk: ${prediction.risk_level}`);
    console.log(`Probability: ${(prediction.probability * 100).toFixed(1)}%`);
});
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 25.7617,
    "longitude": -80.1918,
    "temperature": 28.5,
    "humidity": 75,
    "pressure": 1010.25,
    "wind_speed": 12.5,
    "wind_direction": 200,
    "precipitation": 0.5
  }' | jq
```

---

## Webhooks

To set up alerts when predictions reach HIGH or CRITICAL risk:

```bash
# Register webhook
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/alerts",
    "events": ["prediction_critical", "prediction_high"],
    "active": true
  }'
```

---

**Last Updated:** 2024-02-26
**API Version:** 1.0
