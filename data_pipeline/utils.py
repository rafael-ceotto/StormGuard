"""
Utility Functions
=================
Shared utilities for data pipeline.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    """Configuration management"""
    
    @staticmethod
    def get_minio_config() -> Dict[str, str]:
        """Get MinIO/S3 configuration"""
        return {
            'endpoint': os.getenv('MINIO_ENDPOINT', 'minio:9000'),
            'access_key': os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin'),
            'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin'),
            'bucket': os.getenv('MINIO_BUCKET', 'stormguard-datalake'),
            'secure': False,  # For local development
        }
    
    @staticmethod
    def get_database_config() -> Dict[str, str]:
        """Get PostgreSQL configuration"""
        return {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'airflow'),
            'user': os.getenv('POSTGRES_USER', 'airflow'),
            'password': os.getenv('POSTGRES_PASSWORD', 'airflow'),
        }
    
    @staticmethod
    def get_redis_config() -> Dict[str, str]:
        """Get Redis configuration"""
        return {
            'host': os.getenv('REDIS_HOST', 'redis'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
        }

class DateTimeUtils:
    """Datetime utility functions"""
    
    @staticmethod
    def get_utc_now() -> datetime:
        """Get current UTC time"""
        return datetime.utcnow()
    
    @staticmethod
    def get_date_range(start_date: str, end_date: str) -> List[str]:
        """Generate list of dates between start and end"""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        return dates
    
    @staticmethod
    def get_last_n_hours(n: int) -> str:
        """Get datetime from N hours ago"""
        return (datetime.utcnow() - timedelta(hours=n)).isoformat()

class FileUtils:
    """File I/O utilities"""
    
    @staticmethod
    def ensure_dir_exists(path: str) -> None:
        """Ensure directory exists"""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str) -> None:
        """Save dictionary to JSON file"""
        FileUtils.ensure_dir_exists(os.path.dirname(filepath))
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved JSON to {filepath}")
    
    @staticmethod
    def load_json(filepath: str) -> Dict[str, Any]:
        """Load JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)

class RetryUtils:
    """Retry logic utilities"""
    
    @staticmethod
    def retry_with_backoff(
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ):
        """Retry function with exponential backoff"""
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    import time
                    time.sleep(delay)
                    delay *= backoff_factor
        
        raise last_exception

class ValidationUtils:
    """Data validation utilities"""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """Validate latitude and longitude"""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def validate_temperature(temp: float) -> bool:
        """Validate temperature value"""
        return -50 <= temp <= 60
    
    @staticmethod
    def validate_humidity(humidity: float) -> bool:
        """Validate humidity percentage"""
        return 0 <= humidity <= 100
    
    @staticmethod
    def validate_probability(prob: float) -> bool:
        """Validate probability value"""
        return 0 <= prob <= 1

class MetricsUtils:
    """Metrics calculation utilities"""
    
    @staticmethod
    def calculate_auc(y_true, y_pred) -> float:
        """Calculate ROC-AUC score"""
        from sklearn.metrics import roc_auc_score
        try:
            return float(roc_auc_score(y_true, y_pred))
        except:
            return 0.0
    
    @staticmethod
    def calculate_pr_auc(y_true, y_pred) -> float:
        """Calculate PR-AUC score"""
        from sklearn.metrics import auc, precision_recall_curve
        try:
            precision, recall, _ = precision_recall_curve(y_true, y_pred)
            return float(auc(recall, precision))
        except:
            return 0.0
    
    @staticmethod
    def calculate_brier_score(y_true, y_pred) -> float:
        """Calculate Brier Score (calibration metric)"""
        from sklearn.metrics import brier_score_loss
        try:
            return float(brier_score_loss(y_true, y_pred))
        except:
            return 0.0

class LoggingUtils:
    """Logging utilities"""
    
    @staticmethod
    def setup_logging(name: str, level: str = 'INFO') -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
