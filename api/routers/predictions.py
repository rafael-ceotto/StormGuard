"""
Predictions Router
==================
Endpoints for disaster predictions.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class WeatherInput(BaseModel):
    """Input for prediction"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    temperature: float
    humidity: float = Field(..., ge=0, le=100)
    pressure: float
    wind_speed: float
    wind_direction: int = Field(..., ge=0, le=360)
    precipitation: Optional[float] = 0.0

class DisasterPrediction(BaseModel):
    """Prediction output"""
    disaster_type: str
    probability: float = Field(..., ge=0, le=1)
    risk_level: str
    confidence_interval_lower: float
    confidence_interval_upper: float
    lead_time_hours: int
    location: dict
    prediction_time: datetime

@router.post("/predict", response_model=DisasterPrediction)
async def predict_disaster(data: WeatherInput):
    """
    Get disaster probability for location
    
    Returns probability and risk level for specified location
    """
    logger.info(f"Prediction request: lat={data.latitude}, lon={data.longitude}")
    
    try:
        # In production: Load model from cache/registry and run inference
        # For demo: return mock prediction
        
        pred_prob = 0.35  # Mock probability
        
        if pred_prob < 0.2:
            risk_level = "LOW"
        elif pred_prob < 0.5:
            risk_level = "MEDIUM"
        elif pred_prob < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        return DisasterPrediction(
            disaster_type="flood",
            probability=pred_prob,
            risk_level=risk_level,
            confidence_interval_lower=pred_prob - 0.05,
            confidence_interval_upper=pred_prob + 0.05,
            lead_time_hours=48,
            location={
                "latitude": data.latitude,
                "longitude": data.longitude,
            },
            prediction_time=datetime.utcnow(),
        )
    
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction failed")

@router.post("/predict_batch")
async def predict_batch(locations: List[WeatherInput]):
    """
    Batch predictions for multiple locations
    """
    logger.info(f"Batch prediction for {len(locations)} locations")
    
    predictions = []
    
    for location in locations:
        pred = await predict_disaster(location)
        predictions.append(pred)
    
    return {
        "predictions": predictions,
        "count": len(predictions),
        "timestamp": datetime.utcnow(),
    }

@router.get("/predictions/{location_id}")
async def get_prediction_history(location_id: str, days: int = 7):
    """
    Get prediction history for a location
    """
    logger.info(f"Getting prediction history for {location_id}")
    
    # In production: Query database
    return {
        "location_id": location_id,
        "predictions": [],
        "days": days,
    }
