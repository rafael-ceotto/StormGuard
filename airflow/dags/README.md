# 🚀 StormGuard AI - DAGs

## ✅ DAGs Ativas

Este diretório contém **apenas as 4 DAGs principais** do StormGuard:

### 1. **data_ingestion_dag.py**
- **DAG ID**: `data_ingestion_pipeline`
- **Frequência**: Daily @ 05:00 UTC
- **Função**: Ingesta dados de NOAA, NASA e sensores em tempo real
- **Status**: ✅ Ativo

### 2. **model_training_dag.py**
- **DAG ID**: `model_training_pipeline`
- **Frequência**: Weekly (Mondays @ 03:00 UTC)
- **Função**: Treinamento de modelos CNN-LSTM e Transformer com hyperparameter tuning
- **Status**: ✅ Ativo

### 3. **realtime_inference_dag.py**
- **DAG ID**: `realtime_inference_pipeline`
- **Frequência**: Every 6 hours
- **Função**: Faz predições em tempo real com calibração de probabilidade
- **Status**: ✅ Ativo

### 4. **monitoring_dag.py**
- **DAG ID**: `monitoring_pipeline`
- **Frequência**: Hourly
- **Função**: Health checks, drift detection, performance monitoring
- **Status**: ✅ Ativo

---

## 📋 Estrutura

```
dags/
├── __init__.py                    (Necessário para Python package)
├── data_ingestion_dag.py          (Ingestion pipeline)
├── model_training_dag.py          (Training pipeline)
├── realtime_inference_dag.py      (Inference pipeline)
├── monitoring_dag.py              (Monitoring pipeline)
└── README.md                      (Este arquivo)
```

---

## 🎯 Nenhuma DAG de Exemplo

- ❌ Nenhuma DAG de exemplo ou teste
- ❌ Nenhuma DAG gerada automaticamente
- ❌ Nenhum arquivo de configuração que crie DAGs extras

---

## 💡 Se ver DAGs extras na UI:

1. Limpe o cache: `docker-compose restart airflow-scheduler airflow-webserver`
2. Aguarde 30-60s para o Airflow fazer re-parse dos arquivos
3. F5 para refresh da UI

---

**Versão**: 1.0.0  
**Status**: Pure & Clean ✨
