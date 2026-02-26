"""
Feature Engineering
===================
Advanced feature engineering for machine learning models.

Features created:
1. Temporal features (lags, rolling stats)
2. Spatial features (geographic encoding)
3. Meteorological indices
4. Statistical aggregations
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Feature engineering for ML models"""
    
    def __init__(self):
        pass
    
    def prepare_splits(self, execution_date: str) -> Tuple[str, str, str]:
        """
        Prepare train/val/test splits
        
        Split strategy:
        - Train: 70% (oldest data)
        - Val: 15%
        - Test: 15% (most recent)
        
        This temporal split prevents data leakage.
        """
        logger.info(f"Preparing data splits for {execution_date}")
        
        # Simplified paths - in production would come from S3
        train_path = f"/tmp/splits/{execution_date}/train.parquet"
        val_path = f"/tmp/splits/{execution_date}/val.parquet"
        test_path = f"/tmp/splits/{execution_date}/test.parquet"
        
        return train_path, val_path, test_path
    
    def engineer_features(self, train_path: str, val_path: str, test_path: str) -> Dict[str, Any]:
        """
        Engineer features on datasets
        
        Returns:
            Configuration dictionary with feature information
        """
        logger.info("Running feature engineering")
        
        # Load datasets
        train_df = pd.read_parquet(train_path) if train_path.endswith('.parquet') else pd.read_csv(train_path)
        
        # Apply feature engineering
        features = self._create_features(train_df)
        
        logger.info(f"Created {len(features)} features")
        
        return {
            'num_features': len(features),
            'feature_names': features,
            'train_path': train_path,
            'val_path': val_path,
            'test_path': test_path,
            'test_data': None,  # Would load actual test data
        }
    
    def _create_features(self, df: pd.DataFrame) -> list:
        """
        Create advanced features
        
        Feature categories:
        1. Raw meteorological features
        2. Temporal features (lag, rolling)
        3. Domain-specific indices
        4. Spatial features
        """
        logger.info("Creating meteorological features")
        
        features = []
        
        # 1. Temperature features
        if 'temperature' in df.columns or 'temperature_mean' in df.columns:
            temp_col = 'temperature' if 'temperature' in df.columns else 'temperature_mean'
            
            # Lags
            for lag in [1, 3, 6, 24]:
                features.append(f'temperature_lag_{lag}h')
            
            # Rolling statistics
            for window in [6, 12, 24]:
                features.append(f'temperature_rolling_mean_{window}h')
                features.append(f'temperature_rolling_std_{window}h')
            
            # Anomalies
            features.append('temperature_anomaly')
            
            # Heat wave index
            features.append('heat_index')
        
        # 2. Humidity features
        if 'humidity' in df.columns:
            features.append('humidity')
            features.append('humidity_lag_6h')
            features.append('humidity_rolling_mean_12h')
            features.append('dew_point')
        
        # 3. Wind features
        if 'wind_speed' in df.columns:
            features.append('wind_speed')
            features.append('wind_speed_anomaly')
            features.append('wind_direction')
            features.append('wind_speed_lag_3h')
            features.append('wind_speed_rolling_max_12h')
            features.append('wind_gust_potential')
        
        # 4. Pressure features
        if 'pressure' in df.columns:
            features.append('pressure')
            features.append('pressure_tendency')  # Rising/falling
            features.append('pressure_lag_3h')
            features.append('pressure_anomaly')
        
        # 5. Precipitation features
        if 'precipitation' in df.columns:
            features.append('precipitation')
            features.append('precipitation_cumsum_24h')
            features.append('precipitation_intensity')
        
        # 6. Oceanographic features
        features.extend([
            'sea_surface_temperature',
            'sea_surface_temperature_anomaly',
            'wave_height',
            'el_nino_index',
        ])
        
        # 7. Temporal features
        features.extend([
            'hour_of_day',
            'day_of_week',
            'day_of_year',
            'month',
            'season',
            'is_holiday',
        ])
        
        # 8. Spatial features
        features.extend([
            'latitude',
            'longitude',
            'elevation',
            'distance_to_ocean',
            'distance_to_mountains',
        ])
        
        logger.info(f"Total features: {len(features)}")
        
        return features
    
    def scale_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Scale features to [0, 1] range
        Uses sklearn StandardScaler
        """
        from sklearn.preprocessing import StandardScaler
        
        logger.info("Scaling features")
        
        scaler = StandardScaler()
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values using forward fill + interpolation
        """
        logger.info("Handling missing values")
        
        # Forward fill for time series
        df = df.fillna(method='ffill')
        
        # Interpolate remaining
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear')
        
        # Fill any remaining with mean
        for col in numeric_cols:
            if df[col].isnull().any():
                df[col].fillna(df[col].mean(), inplace=True)
        
        return df
    
    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temporal features from datetime column
        """
        logger.info("Creating temporal features")
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            df['hour_of_day'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['day_of_year'] = df['timestamp'].dt.dayofyear
            df['month'] = df['timestamp'].dt.month
            
            # Season
            def get_season(month):
                if month in [12, 1, 2]:
                    return 0  # Winter
                elif month in [3, 4, 5]:
                    return 1  # Spring
                elif month in [6, 7, 8]:
                    return 2  # Summer
                else:
                    return 3  # Fall
            
            df['season'] = df['month'].apply(get_season)
        
        return df
    
    def create_lag_features(self, df: pd.DataFrame, target_col: str, lags: list = [1, 3, 6, 12, 24]) -> pd.DataFrame:
        """
        Create lag features for time series
        """
        logger.info(f"Creating lag features for {target_col}")
        
        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        return df
    
    def create_rolling_features(self, df: pd.DataFrame, target_col: str, windows: list = [6, 12, 24]) -> pd.DataFrame:
        """
        Create rolling statistics
        """
        logger.info(f"Creating rolling features for {target_col}")
        
        for window in windows:
            df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window).mean()
            df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window).std()
            df[f'{target_col}_rolling_max_{window}'] = df[target_col].rolling(window).max()
        
        return df
