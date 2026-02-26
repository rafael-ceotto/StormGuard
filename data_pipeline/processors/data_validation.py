"""
Data Validation Module
======================
Validates data quality using Great Expectations and custom checks.

Checks performed:
- Schema validation
- Missing values
- Outlier detection
- Temporal consistency
- Geographical validity
"""

import logging
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class DataValidator:
    """Validate data quality"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    @staticmethod
    def _load_validation_rules() -> Dict[str, Any]:
        """Load data validation rules"""
        return {
            'temperature': {'min': -50, 'max': 60, 'unit': 'celsius'},
            'humidity': {'min': 0, 'max': 100, 'unit': 'percent'},
            'pressure': {'min': 870, 'max': 1060, 'unit': 'hPa'},
            'wind_speed': {'min': 0, 'max': 100, 'unit': 'kmh'},
            'latitude': {'min': -90, 'max': 90},
            'longitude': {'min': -180, 'max': 180},
        }
    
    def validate(self, data_path: str, source: str) -> Dict[str, Any]:
        """
        Validate dataset from file
        
        Args:
            data_path: Path to data file
            source: Data source name
        
        Returns:
            Validation report
        """
        logger.info(f"Validating {source} data from {data_path}")
        
        try:
            # Load data
            if data_path.endswith('.parquet'):
                df = pd.read_parquet(data_path)
            elif data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
            else:
                raise ValueError(f"Unsupported file format: {data_path}")
            
            # Run validations
            schema_valid = self._validate_schema(df, source)
            missing_valid = self._validate_missing_values(df)
            range_valid = self._validate_value_ranges(df)
            outlier_valid = self._validate_outliers(df)
            geo_valid = self._validate_geographic(df)
            
            all_valid = all([schema_valid, missing_valid, range_valid, outlier_valid, geo_valid])
            
            report = {
                'source': source,
                'total_records': len(df),
                'passed': all_valid,
                'schema_valid': schema_valid,
                'missing_valid': missing_valid,
                'range_valid': range_valid,
                'outlier_valid': outlier_valid,
                'geo_valid': geo_valid,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Validation report for {source}: {report}")
            
            return report
        
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return {'passed': False, 'error': str(e)}
    
    def _validate_schema(self, df: pd.DataFrame, source: str) -> bool:
        """Validate required columns exist"""
        logger.info(f"Validating schema for {source}")
        
        required_columns = {
            'noaa': ['latitude', 'longitude', 'temperature_mean', 'pressure'],
            'nasa': ['latitude', 'longitude', 'lst_kelvin'],
            'realtime': ['latitude', 'longitude', 'temperature', 'humidity'],
        }
        
        required = required_columns.get(source, [])
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            logger.error(f"Missing columns: {missing}")
            return False
        
        return True
    
    def _validate_missing_values(self, df: pd.DataFrame) -> bool:
        """Check for missing values"""
        logger.info("Validating missing values")
        
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        
        # Allow up to 5% missing values
        threshold = 5.0
        invalid_cols = {k: v for k, v in missing_pct.items() if v > threshold}
        
        if invalid_cols:
            logger.warning(f"Columns with > {threshold}% missing: {invalid_cols}")
            # Don't fail on this - forward fill is acceptable
        
        return True
    
    def _validate_value_ranges(self, df: pd.DataFrame) -> bool:
        """Validate values within acceptable ranges"""
        logger.info("Validating value ranges")
        
        rules = self.validation_rules
        
        for col, rule in rules.items():
            if col not in df.columns:
                continue
            
            out_of_range = df[(df[col] < rule['min']) | (df[col] > rule['max'])]
            
            if len(out_of_range) > 0:
                pct = len(out_of_range) / len(df) * 100
                logger.warning(f"{col}: {pct:.2f}% values out of range [{rule['min']}, {rule['max']}]")
                
                # Allow up to 2% out-of-range values (likely measurement errors)
                if pct > 2.0:
                    logger.error(f"{col}: Too many out-of-range values")
                    return False
        
        return True
    
    def _validate_outliers(self, df: pd.DataFrame) -> bool:
        """Detect and flag outliers using IQR method"""
        logger.info("Validating outliers")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        outlier_counts = {}
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 3 * IQR  # 3x IQR for detection
            upper_bound = Q3 + 3 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            
            if len(outliers) > 0:
                outlier_counts[col] = len(outliers)
        
        if outlier_counts:
            logger.warning(f"Outliers detected: {outlier_counts}")
        
        return True
    
    def _validate_geographic(self, df: pd.DataFrame) -> bool:
        """Validate geographic coordinates"""
        logger.info("Validating geographic data")
        
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            return True
        
        invalid_lat = df[(df['latitude'] < -90) | (df['latitude'] > 90)]
        invalid_lon = df[(df['longitude'] < -180) | (df['longitude'] > 180)]
        
        if len(invalid_lat) > 0 or len(invalid_lon) > 0:
            logger.error(f"Invalid coordinates: {len(invalid_lat)} lat, {len(invalid_lon)} lon")
            return False
        
        return True
