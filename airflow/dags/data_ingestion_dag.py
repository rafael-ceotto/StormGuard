"""
Data Ingestion DAG
==================
Pulls meteorological data from NOAA, NASA, and other sources.
Updates daily with new data.

Frequency: Daily at 05:00 UTC
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.utils.task_group import TaskGroup
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'stormguard-team',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

@dag(
    dag_id='data_ingestion_pipeline',
    default_args=default_args,
    description='Daily data ingestion from NOAA and NASA',
    schedule_interval='0 5 * * *',  # Daily at 05:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['data-pipeline', 'ingestion'],
)
def data_ingestion_pipeline():
    """
    Main data ingestion DAG
    """

    @task
    def ingest_noaa_data(**context):
        """
        Ingest NOAA meteorological data
        Sources: 
        - Historical hurricane tracks
        - Weather observations
        - Radar data
        """
        from data_pipeline.ingestors.noaa_ingestor import NOAAIngestor
        
        ingestor = NOAAIngestor()
        date = context['ds']
        
        logger.info(f"Ingesting NOAA data for {date}")
        
        # Fetch and validate data
        data = ingestor.fetch_daily_data(date)
        stored_path = ingestor.store_to_datalake(data, date)
        
        logger.info(f"NOAA data stored at {stored_path}")
        return stored_path

    @task
    def ingest_nasa_data(**context):
        """
        Ingest NASA satellite imagery
        Sources:
        - MODIS spectral data
        - Land surface temperature
        - Cloud cover
        """
        from data_pipeline.ingestors.nasa_ingestor import NASAIngestor
        
        ingestor = NASAIngestor()
        date = context['ds']
        
        logger.info(f"Ingesting NASA data for {date}")
        
        data = ingestor.fetch_daily_data(date)
        stored_path = ingestor.store_to_datalake(data, date)
        
        logger.info(f"NASA data stored at {stored_path}")
        return stored_path

    @task
    def ingest_realtime_sensors(**context):
        """
        Ingest real-time sensor data
        Sources:
        - Weather stations
        - Ocean buoys
        - Radar networks
        """
        from data_pipeline.ingestors.realtime_ingestor import RealtimeIngestor
        
        ingestor = RealtimeIngestor()
        
        logger.info("Ingesting real-time sensor data")
        
        data = ingestor.fetch_realtime_data()
        stored_path = ingestor.store_to_datalake(data)
        
        logger.info(f"Real-time data stored at {stored_path}")
        return stored_path

    @task
    def validate_data_quality(noaa_path, nasa_path, realtime_path, **context):
        """
        Validate all ingested data using Great Expectations
        Checks:
        - Schema validation
        - Missing values
        - Outlier detection
        - Data consistency
        """
        from data_pipeline.processors.data_validation import DataValidator
        
        validator = DataValidator()
        date = context['ds']
        
        logger.info(f"Validating data quality for {date}")
        
        validation_results = {
            'noaa': validator.validate(noaa_path, 'noaa'),
            'nasa': validator.validate(nasa_path, 'nasa'),
            'realtime': validator.validate(realtime_path, 'realtime'),
        }
        
        # Check if all validations passed
        all_valid = all(v['passed'] for v in validation_results.values())
        
        if not all_valid:
            logger.warning(f"Data validation failed: {validation_results}")
            raise ValueError("Data quality checks failed")
        
        logger.info("Data validation passed")
        return validation_results

    @task
    def merge_and_transform(validation_results, **context):
        """
        Merge data from multiple sources
        Create unified dataset with common schema
        """
        from data_pipeline.processors.preprocessing import DataPreprocessor
        
        preprocessor = DataPreprocessor()
        date = context['ds']
        
        logger.info(f"Merging and transforming data for {date}")
        
        merged_path = preprocessor.merge_datasets(date)
        
        logger.info(f"Merged dataset stored at {merged_path}")
        return merged_path

    @task
    def store_to_datalake(merged_path, **context):
        """
        Store processed data to Data Lake using Delta Lake format
        Maintains ACID properties and versioning
        """
        from data_pipeline.processors.storage import DeltaLakeWriter
        
        writer = DeltaLakeWriter()
        date = context['ds']
        
        logger.info(f"Storing to Delta Lake for {date}")
        
        delta_path = writer.write_to_delta(merged_path, date)
        
        logger.info(f"Data stored to Delta Lake at {delta_path}")
        return delta_path

    @task
    def notify_completion(delta_path, **context):
        """Send completion notification to Slack"""
        message = f"✅ Data ingestion completed for {context['ds']}\nDelta Lake path: {delta_path}"
        logger.info(message)
        # In production, integrate with Slack webhook
        return message

    # Task execution flow
    noaa_data = ingest_noaa_data()
    nasa_data = ingest_nasa_data()
    realtime_data = ingest_realtime_sensors()
    
    validation = validate_data_quality(noaa_data, nasa_data, realtime_data)
    merged = merge_and_transform(validation)
    stored = store_to_datalake(merged)
    notify_completion(stored)

# Instantiate the DAG
data_ingestion_dag = data_ingestion_pipeline()
