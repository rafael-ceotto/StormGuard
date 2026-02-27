# StormGuard AI

**Production-ready AI platform for real-time weather disaster prediction**

## Overview

StormGuard is a distributed machine learning platform for proactive detection of weather disasters (floods, hurricanes, heatwaves, severe storms) using real-time meteorological data and historical patterns.

**Key Features:**
- Real-time predictions with confidence intervals
- Apache Airflow orchestration with alert DAGs
- FastAPI REST API with Redis caching
- TensorFlow deep learning models (CNN-LSTM, Transformers, Ensemble)
- PostgreSQL + S3 data pipeline
- Docker + Kubernetes deployment

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run test suite
python test_suite.py --full

# Start with Docker
docker-compose up -d
```

**Access Points:**
- API: http://localhost:8000/docs
- Airflow: http://localhost:8080 (airflow/airflow)
- MinIO: http://localhost:9001

## Documentation

Complete documentation is in the [md/](md/) folder:

- **[md/QUICKSTART_TESTING.md](md/QUICKSTART_TESTING.md)** - Test everything in 5 minutes
- **[md/IMPLEMENTATION_GUIDE.md](md/IMPLEMENTATION_GUIDE.md)** - API reference & architecture
- **[md/AIRFLOW_INTEGRATION.md](md/AIRFLOW_INTEGRATION.md)** - Airflow setup and DAGs
- **[md/TESTING_GUIDE.md](md/TESTING_GUIDE.md)** - Complete testing guide
- **[md/MANUAL_UI_TESTING.md](md/MANUAL_UI_TESTING.md)** - UI testing procedures
- **[md/WORK_COMPLETE.md](md/WORK_COMPLETE.md)** - Project completion summary

## Technology Stack

**Orchestration:** Apache Airflow 2.7.3, PostgreSQL 15  
**ML/AI:** TensorFlow 2.15, Scikit-learn, LangChain + OpenAI, Pinecone  
**API:** FastAPI 0.104.1, Pydantic, WebSockets  
**Data:** SQLAlchemy, Pandas, Delta Lake  
**Caching:** Redis 7  
**Storage:** MinIO (S3-compatible)  
**Infrastructure:** Docker, Kubernetes, Terraform  
**Testing:** Pytest, Locust  

## Project Structure

```
StormGuard/
├── app/                    # FastAPI application
│   ├── main.py
│   ├── routers/
│   ├── schemas/
│   └── services/
├── pipelines/             # Data ingestion & processing
│   ├── embeddings/
│   └── ingestion/
├── rag/                   # RAG modules
├── Supercar-Intelligence-Platform/  # Parallel ML platform
├── supply_unlimited/      # Django e-commerce backend
├── docker-compose.yml     # Local environment
├── requirements.txt       # Python dependencies
├── test_suite.py         # Automated test suite
└── md/                   # Detailed documentation
    ├── QUICKSTART_TESTING.md
    ├── IMPLEMENTATION_GUIDE.md
    ├── AIRFLOW_INTEGRATION.md
    ├── TESTING_GUIDE.md
    └── [8 more guides]
```

## Testing

```bash
# Run full test suite
python test_suite.py --full

# Run specific module tests
python test_suite.py --api
python test_suite.py --db
python test_suite.py --airflow
```

## Recent Updates

- Fixed test suite encoding issues (Windows compatibility)
- Organized documentation into md/ folder
- Removed redundant monitoring stack (Prometheus/Grafana)
- Installed missing dependencies (requests, sqlalchemy)
- All 10+ commits pushed to GitHub

## License

MIT License

---

**Last Updated:** February 2026 | [View Documentation](md/)
