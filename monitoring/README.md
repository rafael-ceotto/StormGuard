# Monitoring & Observability

Prometheus + Grafana stack for comprehensive monitoring.

## Components

- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Dashboards and visualization (port 3000)
- **Alert Manager** - Alert handling
- **Loki** (optional) - Log aggregation

## Configuration

### prometheus.yml
Scrape configurations for:
- API metrics
- PostgreSQL
- Redis
- Kubernetes
- Airflow

### alert_rules.yml
Alert definitions for:
- High error rates
- Model performance degradation
- Data freshness SLAs
- Drift detection
- Latency issues
- Storage quotas

### grafana_datasources.yml
Data sources:
- Prometheus
- Redis

## Dashboards

Pre-built dashboards (in grafana_dashboards/):
- **Model Performance** - AUC, PR-AUC, Brier score
- **System Health** - CPU, memory, disk
- **Predictions** - Volume, latency, risk distribution
- **Data Quality** - Freshness, drift, validation results

## Access

```bash
# Prometheus
http://localhost:9090

# Grafana
http://localhost:3000
Username: admin
Password: admin (change in production!)
```

## Custom Metrics

Add StormGuard-specific metrics:

```python
from prometheus_client import Counter, Gauge

predictions_total = Counter(
    'stormguard_predictions_total',
    'Total predictions made'
)

model_auc = Gauge(
    'stormguard_model_auc',
    'Current model AUC'
)
```

## Alerts

Active alerts monitored (see alert_rules.yml):
- HighErrorRate (>5% for 5m)
- ModelPerformanceDegraded (AUC < 0.85)
- DataFreshnessSLA (>1h stale)
- DriftDetected
- HighLatency (P95 > 1s)
- StorageQuotaExceeded (>90%)
- DatabaseConnectionPoolExhausted

## Alerting Channels

Configure in AlertManager:
- Slack
- PagerDuty
- Email
- Webhook

See `alertmanager.yml` for configuration.

## Best Practices

1. **Retention** - Keep 15 days of metrics
2. **Scrape Interval** - 15s for most jobs
3. **Alert Evaluation** - 30s intervals
4. **Thresholds** - Based on SLOs
5. **Testing** - Test alerts weekly

## Troubleshooting

```bash
# Check metrics collection
curl http://localhost:9090/api/v1/query?query=up

# View Prometheus targets
http://localhost:9090/targets

# Check alert status
http://localhost:9090/alerts
```
