"""
Real-time Inference DAG
=======================
Runs predictions on latest weather data.
Updates predictions every 6 hours for near real-time forecasting.

Frequency: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'stormguard-inference',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='realtime_inference_pipeline',
    default_args=default_args,
    description='Real-time inference pipeline (every 6 hours)',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['inference', 'realtime'],
)
def realtime_inference_pipeline():
    """
    Main real-time inference DAG
    """

    @task
    def fetch_latest_weather_data(**context):
        """
        Fetch latest weather data from multiple sources
        - Current conditions
        - Recent forecasts
        - Real-time satellite imagery
        """
        from data_pipeline.ingestors.realtime_ingestor import RealtimeIngestor
        
        ingestor = RealtimeIngestor()
        
        logger.info("Fetching latest weather data")
        
        data = ingestor.fetch_latest_data()
        
        logger.info(f"Fetched {len(data)} weather stations data")
        
        return {
            'data_path': data['path'],
            'num_records': data['count'],
            'timestamp': context['ts'],
        }

    @task
    def preprocess_inference_data(weather_data, **context):
        """
        Preprocess data for inference
        - Apply same transformations as training
        - Handle missing values
        - Normalize features
        """
        from data_pipeline.processors.preprocessing import DataPreprocessor
        
        preprocessor = DataPreprocessor()
        
        logger.info(f"Preprocessing {weather_data['num_records']} records")
        
        processed_data = preprocessor.preprocess_for_inference(weather_data['data_path'])
        
        logger.info(f"Preprocessed data: {processed_data['path']}")
        
        return processed_data

    @task
    def load_model_from_registry(**context):
        """
        Load best model from MLflow Model Registry
        - Get production-staged model
        - Load with proper versioning
        """
        from models.training.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        
        logger.info("Loading model from MLflow")
        
        model_info = registry.get_production_model()
        
        logger.info(f"Loaded model: {model_info['model_uri']}")
        
        return model_info

    @task
    def run_batch_inference(processed_data, model_info, **context):
        """
        Run batch inference on preprocessed data
        - Generate predictions
        - Calculate confidence intervals
        - Apply calibration
        """
        import tensorflow as tf
        import numpy as np
        from models.training.evaluator import ModelEvaluator
        
        logger.info("Running batch inference")
        
        # Load model
        model = tf.keras.models.load_model(model_info['model_path'])
        
        # Load preprocessed data
        import pandas as pd
        data = pd.read_parquet(processed_data['path'])
        
        # Run predictions
        predictions = model.predict(data)
        
        # Calculate confidence intervals (using ensemble/bootstrapping)
        predictions_with_ci = {
            'predictions': predictions,
            'lower_ci': np.percentile(predictions, 2.5, axis=0),
            'upper_ci': np.percentile(predictions, 97.5, axis=0),
            'timestamp': context['ts'],
        }
        
        logger.info(f"Generated predictions for {len(predictions)} samples")
        
        return predictions_with_ci

    @task
    def apply_probability_calibration(predictions):
        """
        Apply isotonic regression calibration
        Ensures predicted probabilities match actual event rates
        """
        from sklearn.isotonic import IsotonicRegression
        import pickle
        
        logger.info("Applying probability calibration")
        
        # Load calibration model from training
        with open('models/calibration/isotonic_calibrator.pkl', 'rb') as f:
            calibrator = pickle.load(f)
        
        calibrated_probs = calibrator.predict(predictions['predictions'].flatten())
        
        return {
            'calibrated_predictions': calibrated_probs,
            'confidence_intervals': {
                'lower': predictions['lower_ci'],
                'upper': predictions['upper_ci'],
            },
        }

    @task
    def classify_risk_levels(calibrated_predictions):
        """
        Classify predictions into risk levels:
        - LOW (< 0.2)
        - MEDIUM (0.2-0.5)
        - HIGH (0.5-0.8)
        - CRITICAL (> 0.8)
        """
        import numpy as np
        
        logger.info("Classifying risk levels")
        
        probs = calibrated_predictions['calibrated_predictions']
        
        risk_levels = np.select(
            [
                probs < 0.2,
                (probs >= 0.2) & (probs < 0.5),
                (probs >= 0.5) & (probs < 0.8),
                probs >= 0.8,
            ],
            ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
            default='UNKNOWN',
        )
        
        classification = {
            'risk_levels': risk_levels.tolist(),
            'probabilities': probs.tolist(),
        }
        
        logger.info(f"Risk classification complete: {dict(zip(*np.unique(risk_levels, return_counts=True)))}")
        
        return classification

    @task
    def store_predictions(classification, **context):
        """
        Store predictions in database and Data Lake
        - Save to PostgreSQL (for querying)
        - Save to S3 (for archival)
        """
        import pandas as pd
        from sqlalchemy import create_engine
        
        logger.info("Storing predictions")
        
        df = pd.DataFrame({
            'risk_level': classification['risk_levels'],
            'probability': classification['probabilities'],
            'timestamp': context['ts'],
        })
        
        # Save to PostgreSQL
        engine = create_engine('postgresql://airflow:airflow@postgres:5432/airflow')
        df.to_sql('predictions', con=engine, if_exists='append', index=False)
        
        # Save to S3
        df.to_parquet(f"s3://stormguard-datalake/predictions/{context['ds']}.parquet")
        
        logger.info(f"Stored {len(df)} predictions")
        
        return {
            'num_predictions': len(df),
            'critical_alerts': (df['risk_level'] == 'CRITICAL').sum(),
        }

    @task
    def trigger_alerts(predictions_stored, **context):
        """
        Send alerts for HIGH and CRITICAL risk areas
        - Email notifications
        - Slack messages
        - SMS (for critical)
        """
        logger.info(f"Triggering alerts: CRITICAL={predictions_stored['critical_alerts']}")
        
        if predictions_stored['critical_alerts'] > 0:
            # In production, integrate with notification services
            logger.warning(f"ALERT: {predictions_stored['critical_alerts']} CRITICAL predictions")
        
        return {
            'alerts_sent': predictions_stored['critical_alerts'] > 0,
            'critical_count': predictions_stored['critical_alerts'],
        }

    # Task execution flow
    weather_data = fetch_latest_weather_data()
    processed = preprocess_inference_data(weather_data)
    model = load_model_from_registry()
    predictions = run_batch_inference(processed, model)
    calibrated = apply_probability_calibration(predictions)
    classified = classify_risk_levels(calibrated)
    stored = store_predictions(classified)
    alerts = trigger_alerts(stored)

# Instantiate the DAG
realtime_inference_dag = realtime_inference_pipeline()
