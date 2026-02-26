# Architecture Documentation

## StormGuard AI - System Architecture

### High-Level Overview

StormGuard AI is a production-grade disaster prediction platform that combines:
- **Real-time data ingestion** from NOAA, NASA, and other meteorological sources
- **Advanced ML/DL models** (CNN-LSTM, Transformer) for probabilistic forecasting
- **Distributed processing** with Apache Spark and Airflow
- **Scalable inference API** with FastAPI and Redis caching
- **Comprehensive monitoring** with Prometheus, Grafana, and Evidently AI
- **Cloud-native deployment** with Kubernetes and Terraform

### Data Flow Architecture

```
┌─────────────────────────────┐
│     Data Sources (Real-time) │
│  NOAA|NASA|ECMWF|Satélite   │
└──────────────┬──────────────┘
               │
           (Kafka/Streaming)
               │
        ┌──────▼────────┐
        │ Data Lake (S3)│
        │ + Delta Lake  │
        └──────┬────────┘
               │
    ┌──────────┴──────────┬────────────┐
    │                     │            │
    ▼                     ▼            ▼
┌────────────┐    ┌──────────────┐  ┌───────────┐
│ Training   │    │ Inference    │  │ Monitoring│
│ Pipeline   │    │ Pipeline     │  │ Pipeline  │
└────┬───────┘    └──────┬───────┘  └─────┬─────┘
     │                   │                │
     └───────┬───────────┴────────────────┘
             │
    ┌────────▼────────┐
    │ MLflow Registry │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  FastAPI Server │
    │  + Redis Cache  │
    └─────────────────┘
```

### Component Details

#### 1. Data Ingestion Layer

**NOAA Ingestor:**
- Fetches historical hurricane tracks
- Retrieves GSOD (Global Summary of the Day)
- Sources GOES-16 satellite data

**NASA Ingestor:**
- Collects MODIS reflectance data
- Land surface temperature (LST)
- Cloud properties

**Real-time Ingestor:**
- Weather station networks
- Ocean buoy data
- Radar networks (NEXRAD)

#### 2. Data Processing Layer

**Feature Engineering:**
- Temporal: lags, rolling statistics, differences
- Spatial: geographical encoding, distance features
- Domain: meteorological indices, heat index, wind chill
- Statistical: skewness, kurtosis, quantiles

**Validation:**
- Schema validation
- Range checks
- Outlier detection (IQR)
- Missing value handling

#### 3. ML/DL Models

**CNN-LSTM Hybrid:**
- Input: Satellite images (spatial) + time series (temporal)
- Architecture: Conv2D → MaxPool → LSTM → Dense
- Best for: Discovering spatial patterns in weather

**Temporal Fusion Transformer:**
- Multi-head attention for long-range dependencies
- Variable selection networks
- Best for: Capturing temporal patterns

**Ensemble:**
- Weighted combination of models
- Calibrated probabilities
- Better generalization

#### 4. Inference Pipeline

- Loads latest data every 6 hours
- Runs batch predictions
- Applies probability calibration
- Stores results to database
- Triggers alerts for HIGH/CRITICAL

#### 5. API Layer (FastAPI)

**Endpoints:**
- `POST /api/v1/predict` - Single location prediction
- `POST /api/v1/predict_batch` - Batch predictions
- `GET /api/v1/models` - List available models
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Airflow DAGs

#### data_ingestion_dag
- **Frequency:** Daily at 05:00 UTC
- **Tasks:**
  1. ingest_noaa_data
  2. ingest_nasa_data
  3. ingest_realtime_sensors
  4. validate_data_quality
  5. merge_and_transform
  6. store_to_datalake

#### model_training_dag
- **Frequency:** Weekly on Sundays
- **Tasks:**
  1. prepare_training_data
  2. feature_engineering
  3. hyperparameter_tuning (Optuna)
  4. train_cnn_lstm_model
  5. train_transformer_model
  6. evaluate_models
  7. run_backtesting
  8. register_model_mlflow

#### realtime_inference_dag
- **Frequency:** Every 6 hours
- **Tasks:**
  1. fetch_latest_weather_data
  2. preprocess_data
  3. load_model_from_registry
  4. run_batch_inference
  5. apply_probability_calibration
  6. classify_risk_levels
  7. store_predictions
  8. trigger_alerts

#### monitoring_dag
- **Frequency:** Hourly
- **Tasks:**
  1. check_data_drift
  2. check_model_performance
  3. check_airflow_health
  4. check_data_pipeline_health
  5. check_storage_health
  6. aggregate_metrics
  7. export_to_prometheus
  8. send_alerts_if_needed

### Deployment Architecture

#### Local Development
```
docker-compose up
- Airflow (localhost:8080)
- PostgreSQL (localhost:5432)
- Redis (localhost:6379)
- MinIO (localhost:9000)
- API (localhost:8000)
- Prometheus (localhost:9090)
- Grafana (localhost:3000)
```

#### Kubernetes Production
```
- StormGuard API Deployment (3 replicas, HPA)
- PostgreSQL StatefulSet
- Redis Deployment
- MinIO Deployment
- Prometheus & Grafana
- Airflow Webserver + Scheduler
```

#### Cloud (AWS/GCP/Azure)
```
- EKS/GKE/AKS cluster
- RDS for PostgreSQL
- ElastiCache for Redis
- S3 for data lake
- ECR/Artifact Registry
- CloudWatch/Stackdriver/Monitor
```

### Monitoring & Observability

**Metrics Collected:**
- Request latency
- Model inference time
- Prediction accuracy
- Data freshness
- Model drift (Evidently AI)
- Resource utilization

**Dashboards:**
- Model performance
- Prediction trends
- System health
- Data quality

**Alerts:**
- Data drift detection
- Model performance degradation
- SLA violations
- System resource limits

### Security & Best Practices

- Environment-based configuration
- Secret management (Secrets Manager)
- RBAC for Kubernetes
- Network policies
- Audit logging
- Regular security scanning

### Performance Optimizations

- **Caching:** Redis for cached predictions
- **Batch processing:** Process multiple locations in parallel
- **GPU support:** Optional TensorFlow GPU acceleration
- **Mixed precision:** Faster training with lower memory
- **Feature caching:** Reuse computed features
- **Model versioning:** A/B testing of models

### Scalability

- **Horizontal scaling:** Add API replicas
- **Auto-scaling:** HPA based on CPU/memory
- **Streaming:** Kafka for real-time data
- **Distributed training:** Multi-GPU training
- **Caching layers:** Redis for hotspots

### Disaster Recovery

- **Backups:** Daily PostgreSQL snapshots
- **Replication:** Multi-region deployment
- **Failover:** Automatic pod restart
- **Data versioning:** Delta Lake versioning
- **Model rollback:** MLflow version control

---

**Last Updated:** 2026-02-26
