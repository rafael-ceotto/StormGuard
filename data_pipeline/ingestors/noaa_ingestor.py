"""
NOAA Data Ingestor
==================
Fetches meteorological and hurricane data from NOAA APIs.

Data sources:
- NOAA Hurricane Tracks (historical)
- NOAA Weather Data API
- NOAA Satellite Data
"""

import logging
import requests
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class NOAAIngestor:
    """Ingest data from NOAA sources"""
    
    BASE_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
    
    def __init__(self):
        self.api_key = os.getenv('NOAA_API_KEY', 'demo')  # Use demo API for public access
        self.minio_config = self._get_minio_config()
    
    @staticmethod
    def _get_minio_config() -> Dict[str, str]:
        """Get MinIO configuration"""
        from data_pipeline.utils import Config
        return Config.get_minio_config()
    
    def fetch_daily_data(self, date: str) -> Dict[str, Any]:
        """
        Fetch complete NOAA data for a specific date
        
        Args:
            date: YYYY-MM-DD format
        
        Returns:
            Dictionary with data paths and metadata
        """
        logger.info(f"Fetching NOAA data for {date}")
        
        # Fetch different data types
        station_data = self._fetch_station_data(date)
        satellite_data = self._fetch_satellite_data(date)
        hurricane_data = self._fetch_hurricane_data(date)
        
        return {
            'station_data': station_data,
            'satellite_data': satellite_data,
            'hurricane_data': hurricane_data,
            'date': date,
            'fetch_timestamp': datetime.utcnow().isoformat(),
        }
    
    def _fetch_station_data(self, date: str) -> pd.DataFrame:
        """
        Fetch weather station observations from NOAA
        
        NOAA provides Global Summary of the Day (GSOD) dataset
        Features: Temperature, Precipitation, Wind, Pressure
        """
        logger.info(f"Fetching NOAA station data for {date}")
        
        # This is a simplified example; in production, use proper NOAA API
        # NOAA GSOD format: https://www.ncei.noaa.gov/products/global-summary-of-the-day
        
        year, month, day = date.split('-')
        
        # In production:
        # url = f"{self.BASE_URL}?dataset=daily-summaries&....&token={self.api_key}"
        # response = requests.get(url)
        # Simulate data for demo
        
        data = {
            'station_id': ['USAF0001', 'USAF0002', 'USAF0003'],
            'latitude': [40.7128, 34.0522, 41.8781],
            'longitude': [-74.0060, -118.2437, -87.6298],
            'temperature_mean': [15.2, 22.1, 18.5],
            'temperature_max': [22.1, 28.3, 25.1],
            'temperature_min': [8.3, 16.0, 12.2],
            'pressure': [1013.2, 1014.1, 1012.9],
            'humidity': [65.5, 58.2, 62.1],
            'wind_speed': [12.3, 8.1, 14.2],
            'wind_direction': [200, 180, 220],
            'precipitation': [0.0, 0.5, 0.2],
            'date': date,
        }
        
        df = pd.DataFrame(data)
        logger.info(f"Fetched {len(df)} station records")
        
        return df
    
    def _fetch_satellite_data(self, date: str) -> Dict[str, Any]:
        """
        Fetch NOAA satellite data (GOES-16)
        
        GOES-16 provides:
        - Infrared imagery (10.35 µm)
        - Visible imagery
        - Cloud top temperature
        - Lightning data
        """
        logger.info(f"Fetching NOAA satellite data for {date}")
        
        # Simplified example
        satellite_info = {
            'satellite': 'GOES-16',
            'bands': [1, 2, 3, 10],  # Band numbers
            'resolution': 0.5,  # 0.5 km
            'coverage': 'CONUS',  # Continental US
            'date': date,
            's3_path': f"s3://noaa-goes16/ABI-L2-MCMIPC/2024/{date.replace('-', '/')}",
        }
        
        return satellite_info
    
    def _fetch_hurricane_data(self, date: str) -> pd.DataFrame:
        """
        Fetch historical hurricane track data from NOAA NHC
        
        NOAA National Hurricane Center maintains:
        - Current/historical hurricane tracks
        - Intensity estimates
        - Forecast tracks
        """
        logger.info(f"Fetching NOAA hurricane data for {date}")
        
        # Simplified example - in production use NOAA NHC API
        # https://www.nhc.noaa.gov/data/
        
        hurricane_data = {
            'name': [],
            'latitude': [],
            'longitude': [],
            'max_wind_speed': [],
            'pressure': [],
            'date': [],
        }
        
        # Would fetch actual hurricane data here
        df = pd.DataFrame(hurricane_data)
        
        logger.info(f"Fetched {len(df)} hurricane records")
        
        return df
    
    def store_to_datalake(self, data: Dict[str, Any], date: str) -> str:
        """
        Store ingested data to Data Lake (S3/MinIO)
        
        Args:
            data: Dictionary with data
            date: YYYY-MM-DD format
        
        Returns:
            S3 path where data was stored
        """
        from data_pipeline.utils import FileUtils
        import io
        
        logger.info(f"Storing NOAA data to data lake for {date}")
        
        # For demo, just save to local disk
        # In production, use boto3 for S3
        
        if isinstance(data.get('station_data'), pd.DataFrame):
            # Save as Parquet for efficient storage
            path = f"/tmp/noaa/station_data/{date}/data.parquet"
            FileUtils.ensure_dir_exists(os.path.dirname(path))
            data['station_data'].to_parquet(path)
            logger.info(f"Stored station data to {path}")
        
        return f"s3://stormguard-datalake/noaa/{date}/"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate fetched data quality
        
        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating NOAA data")
        
        if not isinstance(data.get('station_data'), pd.DataFrame):
            logger.error("Station data is not a DataFrame")
            return False
        
        df = data['station_data']
        
        # Check for required columns
        required_cols = ['latitude', 'longitude', 'temperature_mean']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns: {required_cols}")
            return False
        
        # Check for valid coordinates
        from data_pipeline.utils import ValidationUtils
        
        valid_coords = df.apply(
            lambda row: ValidationUtils.validate_coordinates(row['latitude'], row['longitude']),
            axis=1
        ).all()
        
        if not valid_coords:
            logger.error("Invalid coordinates found")
            return False
        
        logger.info("Data validation passed")
        return True
