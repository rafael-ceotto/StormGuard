"""
Comprehensive Project Overview & Quick Reference

## 🎯 Project Structure

StormGuard AI is organized into these main components:

### /airflow
- **dags/** - Apache Airflow DAGs
  - data_ingestion_dag.py - Fetch NOAA, NASA, real-time data
  - model_training_dag.py - Weekly ML training pipeline  
  - realtime_inference_dag.py - 6-hourly predictions
  - monitoring_dag.py - Hourly health checks

### /data_pipeline
- **ingestors/** - Data source integrations
  - noaa_ingestor.py - NOAA weather data
  - nasa_ingestor.py - NASA satellite imagery
  - realtime_ingestor.py - Real-time sensor networks
- **processors/** - Data processing
  - data_validation.py - Quality checks
  - feature_engineering.py - ML feature creation

### /models
- **architectures/** - Deep Learning models
  - cnn_lstm_model.py - Spatial-temporal CNN-LSTM
  - transformer_model.py - Temporal Fusion Transformer
- **training/** - Training pipeline
  - trainer.py - Model training with callbacks
  - evaluator.py - Performance metrics

### /api
- **routers/** - FastAPI endpoints
  - predictions.py - Prediction endpoint
  - health.py - Health checks
  - models.py - Model management
- **main.py** - FastAPI application

### /infra
- **kubernetes/** - K8s manifests
  - deployments/ - API, database deployments
  - services/ - Service definitions
  - configmaps.yaml - Configuration
- **terraform/** - AWS Infrastructure-as-Code
  - main.tf - EKS, RDS, ElastiCache, S3
  - variables.tf - Configuration

### /monitoring
- prometheus.yml - Metrics scraping
- alert_rules.yml - Alert definitions
- grafana_datasources.yml - Dashboard datasources

### /docs
- ARCHITECTURE.md - System design
- API_REFERENCE.md - API endpoints
- DEPLOYMENT.md - Deployment procedures
- GETTING_STARTED.md - Setup guide

### /tests
- unit/ - Unit tests
- integration/ - Integration tests
- e2e/ - End-to-end tests

## 📊 Key Metrics & Monitoring

**API Metrics (Prometheus):**
- Request latency (predicting)
- Error rate
- Model inference time
- Cache hit rate

**ML Metrics:**
- Model AUC
- PR-AUC (precision-recall)
- Brier Score (calibration)
- Lead time accuracy

**System Metrics:**
- Data freshness
- Database connections
- Storage usage
- Data drift (Evidently AI)

## 🚀 Quick Commands

### Local Development
```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f airflow-webserver

# Stop services
docker-compose down
```

### Airflow
```bash
# Trigger DAG
curl -X POST http://localhost:8080/api/v1/dags/{dag_id}/dagRuns

# List DAGs
curl http://localhost:8080/api/v1/dags
```

### API Testing
```bash
# Single prediction
curl -X POST http://localhost:8000/api/v1/predict \\
  -H "Content-Type: application/json" \\
  -d '{...}'

# Batch prediction
curl -X POST http://localhost:8000/api/v1/predict_batch \\
  -H "Content-Type: application/json" \\
  -d '{...}'

# API docs
open http://localhost:8000/docs
```

### Kubernetes
```bash
# Deploy to K8s
kubectl apply -f infra/kubernetes/

# Check status
kubectl get deployments -n stormguard

# View logs
kubectl logs -n stormguard deployment/stormguard-api

# Scale
kubectl scale --replicas=5 deployment/stormguard-api -n stormguard
```

### Terraform
```bash
# Plan infrastructure
terraform plan -var-file=prod.tfvars

# Deploy
terraform apply -var-file=prod.tfvars

# Destroy
terraform destroy -var-file=prod.tfvars
```

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed system design
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API docs
- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Setup instructions
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment

## 🧠 Models Explanation

### CNN-LSTM Hybrid
- **Input:** Satellite images (spatial) + weather time series (temporal)
- **Architecture:** Conv2D → MaxPool → LSTM → Dense → Sigmoid
- **Best for:** Discovering spatial-temporal patterns
- **Training time:** ~2 hours on GPU

### Temporal Fusion Transformer
- **Input:** Weather time series + metadata
- **Architecture:** Self-attention → MultiHeadAttention → FFN
- **Best for:** Long-range temporal dependencies
- **Training time:** ~1 hour on GPU

### Ensemble
- Weighted combination of models
- Calibrated probabilities
- Better generalization than individual models

## 🔄 Data Flow

```
Raw Data (NOAA/NASA) 
    ↓
Data Lake (S3/MinIO)
    ↓
Feature Engineering
    ↓
Train/Val/Test Split
    ↓
Model Training (TensorFlow)
    ↓
MLflow Registry
    ↓
API Inference
    ↓
Predictions + Confidence Intervals
    ↓
Risk Classification (LOW/MEDIUM/HIGH/CRITICAL)
↓
Alerts (Slack/Email)
```

## ⚙️ Airflow DAGs Schedule

| DAG | Frequency | Duration | Purpose |
|-----|-----------|----------|---------|
| data_ingestion | Daily 05:00 UTC | 30min | Fetch new weather data |
| model_training | Weekly Sun 02:00 | 2-3h | Train/validate models |
| realtime_inference | Every 6h | 15min | Make predictions |
| monitoring | Hourly | 5min | Health checks, drift |

## 📈 Performance

- **API latency:** P95 < 100ms (with cache)
- **Batch inference:** ~1000 predictions/min
- **Model accuracy:** AUC > 0.92
- **Data freshness:** < 1 hour old

## 🔐 Security Features

- Environment-based config
- Secret management (AWS Secrets)
- RBAC (Kubernetes)
- Network policies
- Audit logging
- TLS/HTTPS ready

## 📊 Key Endpoints

### API
- `GET /health` - Health check
- `POST /api/v1/predict` - Single prediction
- `POST /api/v1/predict_batch` - Batch predictions
- `GET /api/v1/models` - List models

### Monitoring
- `http://localhost:9090` - Prometheus
- `http://localhost:3000` - Grafana
- `http://localhost:8080` - Airflow

### Data
- `http://localhost:9000` - MinIO (S3)
- `localhost:6379` - Redis
- `localhost:5432` - PostgreSQL

## 🛠️ Troubleshooting

**Issue:** Airflow UI not accessible
- Check: `docker-compose logs airflow-webserver`
- Reset: `docker exec airflow-webserver airflow db reset --yes`

**Issue:** API latency high
- Check: `curl http://localhost:8000/metrics`
- Monitor: Cache hit rate, model load time

**Issue:** Predictions not updating
- Check: `docker logs stormguard-api`
- Verify: Data freshness, model registry

**Issue:** Out of memory
- Increase: Docker memory limit
- Scale: Kubernetes HPA settings

## 📞 Support

For issues:
1. Check logs: `docker-compose logs service-name`
2. Review: [ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. Check: [API_REFERENCE.md](docs/API_REFERENCE.md)
4. Deploy: [DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 📝 Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes to code
3. Run tests: `pytest tests/`
4. Commit: `git commit -am "Add feature"`
5. Push: `git push origin feature/my-feature`
6. Create PR on GitHub

CI/CD will automatically:
- Run linting & type checks
- Execute unit & integration tests
- Build Docker images
- Deploy to staging (optional)

## 🎓 Learning Resources

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [TensorFlow Guide](https://www.tensorflow.org/guide)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Terraform Docs](https://www.terraform.io/docs/)

---

**Last Updated:** 2024-02-26  
**Version:** 1.0.0  
**Maintainer:** Rafael Ceotto
"""
