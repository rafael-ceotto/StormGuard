# 🌪️ StormGuard AI - Plataforma de Predição de Desastres Meteorológicos em Tempo Real

**Nível Senior Production-Ready | Arquitetura Cloud Native**

## 🎯 Visão Geral

StormGuard AI é uma plataforma distribuída de Machine Learning/Deep Learning para predição proativa de desastres meteorológicos com escopo **global**. Usando dados meteorológicos históricos (século atual) combinados com informações em tempo real, o sistema fornece previsões probabilísticas com intervalo de confiança.

### Desastres Modelados
- 🌊 **Enchentes**
- 🌀 **Furacões**
- 🔥 **Ondas de Calor**
- ⛈️ **Tempestades Severas**

---

## 🏗️ Arquitetura de Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (Real-time)                    │
│   NOAA | NASA Earth Data | ECMWF | INMET | Satélite | Sensores │
└─────────────────────────────┬──────────────────────────────────┘
                              │
                   (Message Queue - Kafka)
                              │
            ┌─────────────────▼──────────────────┐
            │      AIRFLOW ORCHESTRATION         │
            │  (PostgreSQL backend)              │
            │  - Scheduling & Monitoring         │
            │  - Retry & SLA Policies            │
            └─────────────────┬──────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
   │Data Ingestion│  │Feature Engineering│  │Data Validation  │
   │ & Validation │  │ (Spark/Pandas)   │  │(Great Expectations)
   └─────────────┘  └──────────────────┘  └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Data Lake (S3)   │
                    │  + Delta Lake      │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
   │  Training   │  │ Model Registry   │  │  Backtesting    │
   │  TensorFlow │  │  (MLflow)        │  │ & Evaluation    │
   └─────────────┘  └──────────────────┘  └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Inference API    │
                    │   (FastAPI)        │
                    │   + Redis Cache    │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  Dashboard  │  │    Alerts        │  │   Metrics       │
│  (Airflow)  │  │  (Slack/Email)   │  │  (Database)     │
   └─────────────┘  └──────────────────┘  └─────────────────┘
```

---

## 🛠️ Technology Stack (Production-Ready)

### Orchestration & Pipeline
- **Apache Airflow 2.x** - Complex DAG orchestration
- **PostgreSQL 14+** - Airflow backend + Metadata Store
- **Apache Spark** - Distributed data processing (Feature Engineering)

### Machine Learning
- **TensorFlow 2.x** - Deep Learning models
- **MLflow** - Model Registry & Experiment Tracking
- **TensorBoard** - Training visualization
- **Optuna** - Hyperparameter Tuning

### Data
- **AWS S3 / MinIO** - Data Lake
- **Delta Lake** - ACID transactions
- **Great Expectations** - Data Quality
- **Pandas, NumPy, Polars** - Data Processing

### API & Inference
- **FastAPI** - High-performance REST API
- **Redis** - Distributed caching
- **Pydantic** - Schema validation
- **Gunicorn + Uvicorn** - Production ASGI

### Infrastructure
- **Docker & Docker-compose** - Containerization
- **Kubernetes** - Container orchestration
- **Terraform** - Infrastructure as Code

### DevOps
- **GitHub Actions** - CI/CD Pipeline
- **pytest + pytest-cov** - Testing
- **flake8, black, mypy** - Code Quality

---

## 📚 Documentation & Guides

**Start Here:**
- **[QUICKSTART_TESTING.md](QUICKSTART_TESTING.md)** - Test everything in 5 minutes
- **[MANUAL_UI_TESTING.md](MANUAL_UI_TESTING.md)** - UI testing with user registration

**Implementation & Architecture:**
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Complete API reference + architecture
- **[AIRFLOW_INTEGRATION.md](AIRFLOW_INTEGRATION.md)** - Airflow setup and alert DAG

**Testing & QA:**
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing guide for all phases
- **[test_suite.py](test_suite.py)** - Automated test suite (Python)

**Planning & Analysis:**
- **[WORK_COMPLETE.md](WORK_COMPLETE.md)** - Summary of completed work
- **[OPTIMIZATION_ANALYSIS.md](OPTIMIZATION_ANALYSIS.md)** - Redundancy analysis and optimizations
- **[FILE_INVENTORY.md](FILE_INVENTORY.md)** - Complete file inventory

---

## 📦 Project Structure

```
StormGuard/
├── airflow/
│   ├── dags/
│   │   ├── data_ingestion_dag.py
│   │   ├── training_pipeline_dag.py
│   │   ├── inference_dag.py
│   │   └── monitoring_dag.py
│   ├── plugins/
│   │   ├── operators/
│   │   └── hooks/
│   ├── logs/
│   └── airflow.cfg
├── data_pipeline/
│   ├── ingestors/
│   │   ├── noaa_ingestor.py
│   │   ├── nasa_ingestor.py
│   │   └── realtime_ingestor.py
│   ├── processors/
│   │   ├── feature_engineering.py
│   │   ├── data_validation.py
│   │   └── preprocessing.py
│   ├── schema_definitions.py
│   └── utils.py
├── models/
│   ├── architectures/
│   │   ├── cnn_lstm_model.py
│   │   ├── transformer_model.py
│   │   └── ensemble_model.py
│   ├── training/
│   │   ├── trainer.py
│   │   ├── callbacks.py
│   │   └── loss_functions.py
│   ├── config.py
│   └── utils.py
├── api/
│   ├── main.py
│   ├── routers/
│   │   ├── predictions.py
│   │   ├── health.py
│   │   └── models.py
│   ├── schemas/
│   │   ├── weather_input.py
│   │   └── prediction_output.py
│   ├── cache.py
│   └── config.py
├── monitoring/
│   ├── metrics.py
│   ├── drift_detection.py
│   └── grafana_dashboards/
├── infra/
│   ├── kubernetes/
│   │   ├── deployments/
│   │   ├── services/
│   │   └── configmaps/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── docker-compose.yml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
├── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
└── .env.example
```

---

## 🚀 Quick Start

### Pré-requisitos
- Docker & Docker-compose
- Python 3.10+
- PostgreSQL 14+
- AWS CLI (optional, para produção)

### 1. Clone e Setup

```bash
git clone https://github.com/rafael-ceotto/StormGuard
cd StormGuard
cp .env.example .env
```

### 2. Docker-compose (Local)

```bash
docker-compose up -d
```

Isso inicia:
- ✅ Airflow (localhost:8080)
- ✅ PostgreSQL (localhost:5432)
- ✅ Redis (localhost:6379)
- ✅ MinIO (localhost:9000)
- ✅ API (localhost:8000)

**Credenciais Airflow:**
- Username: `airflow`
- Password: `airflow`

### 3. Verificar Status

```bash
# Airflow Web UI
open http://localhost:8080

# API Docs
open http://localhost:8000/docs

# MinIO Console
open http://localhost:9001
```

---

## 🧠 Modelos de ML (Arquitetura)

### 1. CNN-LSTM Hybrid (Spatial-Temporal)

Usado para dados satelitais + séries temporais

```python
# Input:
#   - Spatial: Imagens satelitais (64x64x3) → CNN
#   - Temporal: Series temporais (30 steps x 10 features) → LSTM
# Output:
#   - Probabilidade do desastre [0-1]
#   - Risk level (LOW, MEDIUM, HIGH, CRITICAL)
```

### 2. Transformer (Temporal Fusion)

Captura dependências de longo prazo em séries temporais

```python
# Inspirado em: Temporal Fusion Transformer
# Multihead attention para features meteorológicas
# Variable selection network
```

### 3. Graph Neural Networks (GNN)

Modela regiões geográficas como grafo conectado

```python
# Nós: Regions/Grid cells
# Edges: Distância geográfica
# Captura propagação espacial de eventos
```

### 4. Ensemble Híbrido (Production)

Combinação weighted de:
- Modelo físico (simplified Navier-Stokes)
- Modelo Deep Learning (TensorFlow)
- Modelo Bayesiano (Prior estadístico)

---

## 📊 Fontes de Dados (Real-time)

### Históricos (para treinamento)
1. **NOAA (National Oceanic and Atmospheric Administration)**
   - Histórico de furacões (1851-hoje)
   - Séries temporais meteorológicas
   - Imagens satelitais

2. **NASA Earth Data**
   - MODIS imagery
   - Dados oceanográficos

3. **ECMWF (European Center)**
   - ERA5 reanalysis (1950-hoje)
   - Alta resolução espacial

4. **INMET (Brasil)**
   - Dados nacionais Brasil

### Em Tempo Real
- APIs NOAA (Forecast data)
- Satélites (GOES-16, Copernicus)
- Estações meteorológicas
- Dados oceânicos (SST, pressão)

---

## 🔄 Airflow DAGs

### 1. `data_ingestion_dag`
- **Frequency:** Daily (05:00 UTC)
- **Tasks:**
  - `ingest_noaa_data` → Puxa histórico
  - `ingest_nasa_data` → Imagens satelitais
  - `validate_data` → Qualidade
  - `store_to_datalake` → S3

### 2. `training_pipeline_dag`
- **Frequency:** Weekly (Domingo 02:00 UTC)
- **Tasks:**
  - `prepare_features`
  - `split_train_val_test`
  - `train_model`
  - `evaluate_model`
  - `register_model_mlflow`
  - `run_backtesting`

### 3. `inference_dag`
- **Frequency:** 6 hours
- **Tasks:**
  - `fetch_latest_data`
  - `preprocess`
  - `run_inference`
  - `calibration`
  - `publish_predictions`

### 4. `monitoring_dag`
- **Frequency:** Hourly
- **Tasks:**
  - `check_data_drift`
  - `model_performance_check`
  - `alert_if_needed`

---

## 🧪 Testes (Production-Grade)

```bash
# Unit tests
pytest tests/unit -v --cov=.

# Integration tests
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v

# Load testing
locust -f tests/load/locustfile.py
```

---

## 📈 Métricas de Avaliação (Nível Senior)

Não usamos apenas "accuracy". Métricas reais:

1. **ROC AUC** - Discriminação geral
2. **PR AUC** - Precisão-recall (desbalanceado)
3. **Brier Score** - Calibração de probabilidade
4. **Expected Cost** - Custo esperado do erro
5. **Lead Time** - Tempo de antecedência
6. **False Alarm Ratio (FAR)** - Taxa de alarmes falsos
7. **Hit Rate** - Taxa de detecção correta

---

## 🔐 Segurança & Best Practices

- ✅ Environment variables (.env)
- ✅ Secret management (AWS Secrets Manager / HashiCorp Vault)
- ✅ API Key authentication
- ✅ Role-Based Access Control (RBAC)
- ✅ Data encryption at rest & in transit
- ✅ Audit logging
- ✅ Regular security scans (Trivy)

---

## 📚 Documentação Completa

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detalhes técnicos
- [API_REFERENCE.md](docs/API_REFERENCE.md) - Endpoints da API
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deploy em produção
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - Guia de contribuição
- [DATA_SOURCES.md](docs/DATA_SOURCES.md) - Integração com APIs

---

## 🚀 Deployment

### Local
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f infra/kubernetes/
```

### AWS EKS
```bash
# Deploy via Terraform
cd infra/terraform
terraform apply
```

---

## 🔗 Links Úteis

- 📖 [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- 📖 [TensorFlow Documentation](https://www.tensorflow.org/docs)
- 📖 [FastAPI Documentation](https://fastapi.tiangolo.com/)
- 🗂️ [MLflow Documentation](https://mlflow.org/docs/latest/)

---

## 📝 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes

---

## 👨‍💼 Autor

Rafael Ceotto

---

**Status:** 🚧 Em Desenvolvimento (Fase 1: Arquitetura & Setup)

Last Updated: 2026-02-26
