"""
Pydantic Schemas for User Management
====================================
Data validation schemas for API endpoints
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ===== USER SCHEMAS =====

class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    full_name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    interests: Optional[List[str]] = ["hurricane", "heat_wave", "flood"]
    
    @validator('interests')
    def validate_interests(cls, v):
        valid = {"hurricane", "heat_wave", "flood", "severe_storm", "tornado", "wildfire"}
        if not all(i in valid for i in v):
            raise ValueError(f"Invalid interests. Choose from {valid}")
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    city: Optional[str] = None
    timezone: Optional[str] = None
    notification_token: Optional[str] = None
    notification_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    full_name: Optional[str]
    latitude: float
    longitude: float
    city: Optional[str]
    country: Optional[str]
    timezone: str
    interests: str
    notification_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# ===== PREFERENCE SCHEMAS =====

class UserPreferenceRequest(BaseModel):
    """User preference update schema"""
    hurricane_alerts: Optional[bool] = None
    heat_wave_alerts: Optional[bool] = None
    flood_alerts: Optional[bool] = None
    severe_storm_alerts: Optional[bool] = None
    min_risk_level: Optional[str] = None
    alert_radius_km: Optional[int] = Field(None, ge=10, le=500)
    max_daily_alerts: Optional[int] = Field(None, ge=1, le=100)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    enable_push: Optional[bool] = None
    enable_email: Optional[bool] = None
    enable_sms: Optional[bool] = None


class UserPreferenceResponse(BaseModel):
    """User preference response schema"""
    user_id: str
    hurricane_alerts: bool
    heat_wave_alerts: bool
    flood_alerts: bool
    severe_storm_alerts: bool
    min_risk_level: str
    alert_radius_km: int
    max_daily_alerts: int
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    enable_push: bool
    enable_email: bool
    enable_sms: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== ALERT SCHEMAS =====

class AlertResponse(BaseModel):
    """Alert response schema"""
    id: str
    user_id: str
    disaster_type: str
    title: str
    message: str
    risk_level: str
    risk_score: float
    latitude: float
    longitude: float
    radius_km: int
    sent: bool
    read: bool
    clicked: bool
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    """Create alert schema"""
    user_id: str
    disaster_type: str
    title: str
    message: str
    risk_level: str
    risk_score: float = Field(..., ge=0, le=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: int = Field(default=100, ge=10, le=500)


# ===== CHAT SCHEMAS =====

class ChatMessageRequest(BaseModel):
    """Chat message request schema"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    location_context: Optional[dict] = None  # Optional: {"latitude": X, "longitude": Y}


class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    id: str
    user_message: str
    assistant_response: str
    sources: Optional[List[str]]
    tokens_used: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatFull(BaseModel):
    """Full chat with context"""
    message: str
    response: str
    sources: Optional[List[str]]
    risk_level: Optional[str] = None  # If response includes threat assessment
    timestamp: datetime
