# 🌪️ StormGuard AI - Getting Started Guide

## Quick Start (Development)

### Prerequisites
- Docker & Docker-compose
- Python 3.10+
- Git

### 1. Clone Repository
```bash
git clone https://github.com/rafael-ceotto/StormGuard
cd StormGuard
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your API keys (optional for demo)
```

### 3. Start Services
```bash
docker-compose up -d
```

This starts:
- **Airflow Web UI:** http://localhost:8080
  - Username: `airflow`
  - Password: `airflow`
- **API Docs:** http://localhost:8000/docs
- **Grafana:** http://localhost:3000
  - Username: `admin`
  - Password: `admin`
- **MinIO Console:** http://localhost:9001
  - Username: `minioadmin`
  - Password: `minioadmin`

### 4. Run DAGs

#### Data Ingestion
```bash
curl -X POST http://localhost:8080/api/v1/dags/data_ingestion_pipeline/dagRuns
```

#### Training Pipeline
```bash
curl -X POST http://localhost:8080/api/v1/dags/model_training_pipeline/dagRuns
```

#### Inference
```bash
curl -X POST http://localhost:8080/api/v1/dags/realtime_inference_pipeline/dagRuns
```

### 5. Test API

```bash
# Single prediction
curl -X POST "http://localhost:8000/api/v1/predict" \
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
  }'

# Health check
curl http://localhost:8000/health
```

## Production Deployment

### AWS Deployment

#### Prerequisites
- AWS Account
- Terraform
- kubectl

#### 1. Deploy Infrastructure
```bash
cd infra/terraform

# Create state backend
aws s3 mb s3://stormguard-terraform-state-${AWS_ACCOUNT_ID}
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Deploy
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
```

#### 2. Deploy Applications
```bash
# Build and push Docker images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

docker build -f Dockerfile.api -t ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/stormguard/api:latest .
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/stormguard/api:latest

# Configure kubectl
aws eks update-kubeconfig --name stormguard-prod --region us-east-1

# Deploy to Kubernetes
kubectl apply -f infra/kubernetes/configmaps.yaml
kubectl apply -f infra/kubernetes/deployments/postgres.yaml
kubectl apply -f infra/kubernetes/deployments/api.yaml
```

#### 3. Setup Monitoring
```bash
# Prometheus and Grafana
kubectl apply -f monitoring/prometheus.yaml
kubectl apply -f monitoring/grafana.yaml

# Get Grafana password
kubectl get secret -n stormguard grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

## Data Integration

### NOAA Data
Set your API key:
```bash
export NOAA_API_KEY="your-key"
```

### NASA Data
Set your API key:
```bash
export NASA_API_KEY="your-key"
```

## Troubleshooting

### Airflow won't start
```bash
# Check PostgreSQL
docker logs stormguard-postgres

# Check Airflow webserver
docker logs stormguard-airflow-webserver

# Reset Airflow DB
docker exec stormguard-airflow-webserver airflow db reset --yes
```

### API is slow
- Check Redis connection: `redis-cli -h redis ping`
- Monitor CPU/Memory: `docker stats`
- Check model loaded: `curl http://localhost:8000/api/v1/models`

### Data pipeline failing
- Check data quality: `docker logs stormguard-api`
- Verify API keys are set
- Check PostgreSQL connection

## Configuration

### Environment Variables
See `.env.example` for all available options.

Key variables:
- `AIRFLOW_HOME`: Airflow directory
- `POSTGRES_DB`: Database name
- `REDIS_URL`: Redis connection
- `MINIO_BUCKET`: Data lake bucket
- `NOAA_API_KEY`: NOAA API key
- `NASA_API_KEY`: NASA API key

## Monitoring

### Dashboards
- **Airflow:** http://localhost:8080
- **Grafana:** http://localhost:3000
- **Prometheus:** http://localhost:9090

### Metrics
- Prediction latency
- Model performance (AUC, PR-AUC)
- Data freshness
- System health

## Next Steps

1. Configure API keys for real data sources
2. Set up cloud deployment (AWS/GCP/Azure)
3. Configure alerting (Slack, PagerDuty, etc)
4. Customize models for your usecase
5. Setup CI/CD pipeline

## Support

For issues:
1. Check logs: `docker-compose logs -f service-name`
2. Review [ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. Check [API Reference](docs/API_REFERENCE.md)

## License

MIT License - See LICENSE file
