"""
NASA Data Ingestor
==================
Fetches satellite imagery and earth observation data from NASA.

Data sources:
- MODIS (Moderate Resolution Imaging Spectroradiometer)
- NASA Earth Data API
- Land surface temperature
- Cloud cover and patterns
"""

import logging
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class NASAIngestor:
    """Ingest data from NASA sources"""
    
    BASE_URL = "https://api.nasa.gov"
    
    def __init__(self):
        self.api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
        self.minio_config = self._get_minio_config()
    
    @staticmethod
    def _get_minio_config() -> Dict[str, str]:
        """Get MinIO configuration"""
        from data_pipeline.utils import Config
        return Config.get_minio_config()
    
    def fetch_daily_data(self, date: str) -> Dict[str, Any]:
        """
        Fetch complete NASA satellite data for a specific date
        
        Args:
            date: YYYY-MM-DD format
        
        Returns:
            Dictionary with data paths and metadata
        """
        logger.info(f"Fetching NASA data for {date}")
        
        # Fetch different data products
        modis_data = self._fetch_modis_data(date)
        lst_data = self._fetch_land_surface_temperature(date)
        cloud_data = self._fetch_cloud_data(date)
        
        return {
            'modis': modis_data,
            'land_surface_temperature': lst_data,
            'cloud_cover': cloud_data,
            'date': date,
            'fetch_timestamp': datetime.utcnow().isoformat(),
        }
    
    def _fetch_modis_data(self, date: str) -> Dict[str, Any]:
        """
        Fetch MODIS spectral data
        
        MODIS provides:
        - 36 spectral bands
        - 250m to 1km resolution
        - Reflectance and radiance data
        
        Useful for:
        - Vegetation indices (NDVI)
        - Fire detection
        - Case surface temperature
        """
        logger.info(f"Fetching MODIS data for {date}")
        
        # Simplified example
        # In production: Use NASA's OPeNDAP or GEE
        
        modis_info = {
            'satellite': 'MODIS',
            'platforms': ['Terra', 'Aqua'],
            'bands': list(range(1, 37)),  # 36 bands
            'resolution_m': [250, 250, 250],  # VIS bands at 250m
            'coverage': 'Global',
            'date': date,
            'collections': [
                'MOD09A1',  # Surface reflectance
                'MOD11A1',  # Land surface temperature
                'MOD13A1',  # Vegetation indices
            ],
            's3_path': f"s3://nasa-modis/data/{date.replace('-', '/')}",
        }
        
        return modis_info
    
    def _fetch_land_surface_temperature(self, date: str) -> pd.DataFrame:
        """
        Fetch MODIS Land Surface Temperature (LST)
        
        LST is crucial for:
        - Heat wave detection and prediction
        - Drought monitoring
        - Urban heat island detection
        
        Resolution: 1 km daily
        """
        logger.info(f"Fetching MODIS LST for {date}")
        
        # Simplified: generate synthetic LST data
        # In production: Use NASA's API or LAADS DAAC
        
        latitudes = np.linspace(-90, 90, 180)
        longitudes = np.linspace(-180, 180, 360)
        
        lst_data = {
            'latitude': np.random.choice(latitudes, 1000),
            'longitude': np.random.choice(longitudes, 1000),
            'lst_kelvin': np.random.normal(300, 15, 1000),  # K
            'lst_celsius': np.random.normal(27, 15, 1000),  # °C
            'quality_flag': np.random.randint(0, 5, 1000),
            'date': date,
        }
        
        df = pd.DataFrame(lst_data)
        
        logger.info(f"Fetched {len(df)} LST pixels")
        
        return df
    
    def _fetch_cloud_data(self, date: str) -> Dict[str, Any]:
        """
        Fetch cloud cover and cloud top properties
        
        Useful for:
        - Storm system identification
        - Convective potential estimation
        - Visibility assessment
        """
        logger.info(f"Fetching cloud data for {date}")
        
        cloud_info = {
            'cloud_product': 'MOD35',  # Cloud mask
            'cloud_height_product': 'MOD06',
            'resolution_km': 1.0,
            'bands': [31],  # 11 µm thermal infrared
            'date': date,
            's3_path': f"s3://nasa-modis/cloud/{date.replace('-', '/')}",
        }
        
        return cloud_info
    
    def store_to_datalake(self, data: Dict[str, Any], date: str) -> str:
        """
        Store ingested data to Data Lake
        
        Args:
            data: Dictionary with data
            date: YYYY-MM-DD format
        
        Returns:
            S3 path where data was stored
        """
        from data_pipeline.utils import FileUtils
        import os
        
        logger.info(f"Storing NASA data to data lake for {date}")
        
        # Save LST data as Parquet
        if isinstance(data.get('land_surface_temperature'), pd.DataFrame):
            path = f"/tmp/nasa/lst/{date}/data.parquet"
            FileUtils.ensure_dir_exists(os.path.dirname(path))
            data['land_surface_temperature'].to_parquet(path)
            logger.info(f"Stored LST data to {path}")
        
        return f"s3://stormguard-datalake/nasa/{date}/"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate fetched NASA data
        
        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating NASA data")
        
        # Validate LST data
        if isinstance(data.get('land_surface_temperature'), pd.DataFrame):
            df = data['land_surface_temperature']
            
            # Check for required columns
            required_cols = ['latitude', 'longitude', 'lst_kelvin']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns")
                return False
            
            # Check for valid temperature range (K)
            if not (df['lst_kelvin'] > 0).all():
                logger.error("Invalid temperature values (must be in Kelvin)")
                return False
        
        logger.info("Data validation passed")
        return True
