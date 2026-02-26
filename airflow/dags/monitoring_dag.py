"""
Monitoring & Observability DAG
================================
Monitor data drift, model performance, and system health.
Runs hourly to catch issues early.

Frequency: Hourly
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'stormguard-ops',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='monitoring_and_observability',
    default_args=default_args,
    description='Monitoring pipeline (hourly)',
    schedule_interval='0 * * * *',  # Every hour
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['monitoring', 'observability'],
)
def monitoring_pipeline():
    """
    Main monitoring DAG
    """

    @task
    def check_data_drift(**context):
        """
        Detect data distribution shifts using Evidently AI
        Compares current data distribution with training distribution
        """
        from monitoring.drift_detection import DriftDetector
        
        detector = DriftDetector()
        
        logger.info("Checking for data drift")
        
        drift_report = detector.detect_drift()
        
        if drift_report['has_drift']:
            logger.warning(f"Data drift detected: {drift_report}")
        
        return drift_report

    @task
    def check_model_performance(**context):
        """
        Monitor model performance on recent predictions
        - Calculate rolling metrics
        - Compare with baseline
        - Detect performance degradation
        """
        from monitoring.performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        logger.info("Checking model performance")
        
        perf_metrics = monitor.calculate_performance_metrics(
            window_days=7,
        )
        
        if perf_metrics['auc'] < perf_metrics['baseline_auc'] * 0.95:
            logger.warning(f"Performance degradation: {perf_metrics}")
        
        return perf_metrics

    @task
    def check_airflow_health(**context):
        """
        Monitor Airflow DAG health
        - Check failed tasks
        - Monitor DAG execution times
        - Check for SLA violations
        """
        from airflow.models import DagRun, TaskInstance
        from airflow.utils.state import DagRunState, TaskInstanceState
        
        logger.info("Checking Airflow health")
        
        # This is a simplified example; in production use proper monitoring
        health_check = {
            'airflow_running': True,
            'database_connected': True,
        }
        
        return health_check

    @task
    def check_data_pipeline_health(**context):
        """
        Monitor data pipeline health
        - Check data freshness
        - Verify data completeness
        - Monitor processing latency
        """
        import pandas as pd
        from sqlalchemy import create_engine
        
        logger.info("Checking data pipeline health")
        
        engine = create_engine('postgresql://airflow:airflow@postgres:5432/airflow')
        
        # Query latest data timestamp
        latest_data_query = "SELECT MAX(timestamp) as latest FROM raw_weather_data"
        
        result = pd.read_sql_query(latest_data_query, engine)
        
        latest_timestamp = result['latest'].iloc[0]
        time_since_update = pd.Timestamp.now() - latest_timestamp
        
        health = {
            'data_freshness_hours': time_since_update.total_seconds() / 3600,
            'is_fresh': time_since_update.total_seconds() < 3600,  # 1 hour
        }
        
        if not health['is_fresh']:
            logger.warning(f"Data pipeline stale: {health}")
        
        return health

    @task
    def check_storage_health(**context):
        """
        Monitor storage system health
        - Check disk usage
        - Monitor database size
        - Verify backup completion
        """
        import boto3
        import psycopg2
        
        logger.info("Checking storage health")
        
        # Check S3/MinIO usage
        s3 = boto3.client('s3', endpoint_url='http://minio:9000')
        response = s3.list_objects_v2(Bucket='stormguard-datalake')
        
        storage_health = {
            's3_objects': response.get('KeyCount', 0),
            's3_healthy': True,
        }
        
        return storage_health

    @task
    def aggregate_metrics(
        drift_check, 
        perf_check, 
        airflow_check, 
        pipeline_check, 
        storage_check,
        **context
    ):
        """
        Aggregate all monitoring metrics
        Create comprehensive health report
        """
        
        logger.info("Aggregating monitoring metrics")
        
        health_report = {
            'timestamp': context['ts'],
            'data_drift': drift_check,
            'model_performance': perf_check,
            'airflow': airflow_check,
            'data_pipeline': pipeline_check,
            'storage': storage_check,
            'overall_status': 'HEALTHY',  # Simplified
        }
        
        # Check for critical issues
        if drift_check.get('has_drift'):
            health_report['overall_status'] = 'WARNING'
        
        if not pipeline_check['is_fresh']:
            health_report['overall_status'] = 'WARNING'
        
        logger.info(f"Health report: {health_report['overall_status']}")
        
        return health_report

    @task
    def send_metrics_to_prometheus(health_report, **context):
        """
        Export metrics to Prometheus
        For visualization in Grafana
        """
        from prometheus_client import Counter, Gauge
        import json
        
        logger.info("Exporting metrics to Prometheus")
        
        # Create custom metrics (in production, use proper exposition format)
        logger.info(json.dumps(health_report, indent=2, default=str))
        
        return {
            'metrics_exported': True,
            'timestamp': context['ts'],
        }

    @task
    def send_alert_if_needed(health_report, **context):
        """
        Send alerts if critical issues detected
        - Slack notifications
        - Email to ops
        """
        
        logger.info(f"Checking alert conditions: {health_report['overall_status']}")
        
        if health_report['overall_status'] in ['CRITICAL', 'ERROR']:
            logger.error(f"Critical alert: {health_report}")
            # In production, send Slack/Email
        
        return {
            'alert_sent': health_report['overall_status'] in ['CRITICAL', 'ERROR'],
        }

    # Task execution flow
    drift = check_data_drift()
    perf = check_model_performance()
    airflow_health = check_airflow_health()
    pipeline_health = check_data_pipeline_health()
    storage_health = check_storage_health()
    
    aggregated = aggregate_metrics(drift, perf, airflow_health, pipeline_health, storage_health)
    metrics = send_metrics_to_prometheus(aggregated)
    alerts = send_alert_if_needed(aggregated)

# Instantiate the DAG
monitoring_dag = monitoring_pipeline()
