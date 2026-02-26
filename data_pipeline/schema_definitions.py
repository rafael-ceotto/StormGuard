"""
Schema Definitions
==================
Defines data schemas for all datasets using Pydantic.
Ensures data consistency across the pipeline.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DisasterType(str, Enum):
    """Enum for disaster types"""
    HURRICANE = "hurricane"
    FLOOD = "flood"
    HEAT_WAVE = "heat_wave"
    SEVERE_STORM = "severe_storm"

class RiskLevel(str, Enum):
    """Enum for risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ===== WEATHER DATA SCHEMAS =====

class TemperatureRecord(BaseModel):
    """Temperature measurement"""
    value: float = Field(..., ge=-50, le=60)  # Celsius
    unit: str = "celsius"
    measurement_time: datetime

class PressureRecord(BaseModel):
    """Atmospheric pressure measurement"""
    value: float = Field(..., ge=870, le=1060)  # hPa
    unit: str = "hPa"
    measurement_time: datetime

class HumidityRecord(BaseModel):
    """Relative humidity measurement"""
    value: float = Field(..., ge=0, le=100)  # Percentage
    unit: str = "percent"
    measurement_time: datetime

class WindRecord(BaseModel):
    """Wind speed and direction"""
    speed: float = Field(..., ge=0)  # km/h
    direction: int = Field(..., ge=0, le=360)  # Degrees
    gust_speed: Optional[float] = None
    unit: str = "kmh"
    measurement_time: datetime

class PrecipitationRecord(BaseModel):
    """Precipitation measurement"""
    value: float = Field(..., ge=0)  # mm
    type: str  # rain, snow, sleet
    unit: str = "mm"
    measurement_time: datetime

class WeatherObservation(BaseModel):
    """Complete weather observation"""
    station_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    temperature: TemperatureRecord
    pressure: PressureRecord
    humidity: HumidityRecord
    wind: WindRecord
    precipitation: Optional[PrecipitationRecord] = None
    cloud_cover: Optional[float] = Field(None, ge=0, le=100)
    visibility: Optional[float] = None  # km
    observation_time: datetime
    data_source: str  # noaa, ecmwf, inmet, etc
    
    @validator('observation_time')
    def validate_time(cls, v):
        """Ensure observation time is not in future"""
        if v > datetime.utcnow():
            raise ValueError('Observation time cannot be in future')
        return v

# ===== SATELLITE DATA SCHEMAS =====

class SatelliteImage(BaseModel):
    """Satellite imagery metadata"""
    satellite_name: str
    product_name: str
    latitude_range: tuple  # (min, max)
    longitude_range: tuple  # (min, max)
    resolution_meters: float
    bands: List[int]  # Band numbers
    capture_time: datetime
    data_path: str  # S3 path

# ===== HISTORICAL DISASTER SCHEMAS =====

class HistoricalDisaster(BaseModel):
    """Historical disaster record"""
    disaster_type: DisasterType
    start_date: datetime
    end_date: datetime
    latitude_range: tuple
    longitude_range: tuple
    severity_scale: float = Field(..., ge=0, le=5)
    deaths: int = Field(..., ge=0)
    affected_people: int = Field(..., ge=0)
    economic_damage_usd: float = Field(..., ge=0)
    data_source: str

# ===== FEATURE SCHEMAS =====

class MeteorologicalFeatures(BaseModel):
    """Meteorological features for modeling"""
    # Raw features
    temperature: float
    temperature_anomaly: float
    pressure: float
    pressure_tendency: float
    humidity: float
    wind_speed: float
    wind_speed_anomaly: float
    wind_direction: int
    precipitation: float
    
    # Temporal features (lags)
    temp_lag_1h: Optional[float] = None
    temp_lag_3h: Optional[float] = None
    temp_lag_6h: Optional[float] = None
    temp_lag_24h: Optional[float] = None
    
    # Rolling statistics
    temp_rolling_mean_6h: Optional[float] = None
    temp_rolling_std_6h: Optional[float] = None
    wind_rolling_max_12h: Optional[float] = None
    
    # Domain-specific meteorological indices
    heat_index: Optional[float] = None  # For heat waves
    apparent_temperature: Optional[float] = None
    wet_bulb_globe_temperature: Optional[float] = None
    wind_chill: Optional[float] = None

class OceanographicFeatures(BaseModel):
    """Oceanographic features"""
    sea_surface_temperature: Optional[float] = None
    sea_surface_temperature_anomaly: Optional[float] = None
    sea_level_anomaly: Optional[float] = None
    wave_height: Optional[float] = None
    current_speed: Optional[float] = None
    el_nino_index: Optional[float] = None  # -2 to 2
    la_nina_index: Optional[float] = None

class GeographicalFeatures(BaseModel):
    """Geographical and topographical features"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation: Optional[float] = None  # meters
    land_use_type: Optional[str] = None  # urban, rural, forest, water
    distance_to_ocean: Optional[float] = None  # km
    distance_to_mountains: Optional[float] = None

class TemporalFeatures(BaseModel):
    """Temporal features"""
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    day_of_year: int = Field(..., ge=1, le=366)
    month: int = Field(..., ge=1, le=12)
    season: str  # spring, summer, fall, winter
    is_holiday: bool = False

class ModelInputFeatures(BaseModel):
    """Complete feature set for model input"""
    meteorological: MeteorologicalFeatures
    oceanographic: OceanographicFeatures
    geographical: GeographicalFeatures
    temporal: TemporalFeatures
    timestamp: datetime
    location_id: str

# ===== PREDICTION SCHEMAS =====

class DisasterPrediction(BaseModel):
    """Disaster prediction output"""
    disaster_type: DisasterType
    probability: float = Field(..., ge=0, le=1)
    risk_level: RiskLevel
    confidence_interval_lower: float
    confidence_interval_upper: float
    lead_time_hours: int
    location_id: str
    latitude: float
    longitude: float
    prediction_time: datetime
    valid_until: datetime
    model_version: str

class BatchPredictionOutput(BaseModel):
    """Batch prediction results"""
    predictions: List[DisasterPrediction]
    total_high_risk_areas: int
    total_critical_areas: int
    generated_at: datetime

# ===== DATA QUALITY SCHEMAS =====

class DataQualityReport(BaseModel):
    """Data quality assessment"""
    dataset_name: str
    total_records: int
    valid_records: int
    invalid_records: int
    missing_values_percent: float
    outliers_detected: int
    schema_validation_passed: bool
    timestamp: datetime
    notes: Optional[List[str]] = None
