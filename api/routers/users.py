"""
User Management Router for StormGuard API
=========================================
User profile and preference management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.schemas.user import (
    UserUpdate,
    UserResponse,
    UserPreferenceRequest,
    UserPreferenceResponse
)
from api.utils.auth import get_current_user
from api.utils.db import get_db
from data_pipeline.db_models import User, UserPreference
from datetime import datetime


router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)


@router.get(
    "/{user_id}",
    response_model=dict,
    summary="Get user profile",
    description="Retrieve user profile information"
)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user profile information
    
    **Path Parameters:**
    - user_id: str - User unique identifier
    
    **Security:**
    - Requires valid JWT token
    
    **Returns:**
    - User profile data with all fields
    """
    
    # Verify user is requesting their own profile or is admin
    if current_user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's profile"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "city": user.city,
        "country": user.country,
        "timezone": user.timezone,
        "interests": user.interests,
        "notification_enabled": user.notification_enabled,
        "notification_token": user.notification_token,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login,
    }


@router.put(
    "/{user_id}",
    response_model=dict,
    summary="Update user profile",
    description="Update user profile information"
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update user profile information
    
    **Path Parameters:**
    - user_id: str - User unique identifier
    
    **Request Body:**
    - full_name: Optional[str]
    - latitude: Optional[float]
    - longitude: Optional[float]
    - city: Optional[str]
    - timezone: Optional[str]
    - notification_token: Optional[str] - FCM device token
    - notification_enabled: Optional[bool]
    
    **Security:**
    - Requires valid JWT token
    - Can only update own profile
    
    **Returns:**
    - Updated user profile
    """
    
    # Verify user is updating their own profile
    if current_user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other user's profile"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields if provided
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "city": user.city,
        "country": user.country,
        "timezone": user.timezone,
        "interests": user.interests,
        "notification_enabled": user.notification_enabled,
        "notification_token": user.notification_token,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login,
    }


@router.get(
    "/{user_id}/preferences",
    response_model=dict,
    summary="Get user preferences",
    description="Retrieve user disaster alert preferences"
)
async def get_preferences(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user alert preferences
    
    **Path Parameters:**
    - user_id: str - User unique identifier
    
    **Security:**
    - Requires valid JWT token
    
    **Returns:**
    - User preferences data
    """
    
    # Verify access
    if current_user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's preferences"
        )
    
    # Get or create preferences
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        # Create default preferences for new user
        preferences = UserPreference(
            user_id=user_id,
            hurricane_alerts=True,
            heat_wave_alerts=True,
            flood_alerts=True,
            severe_storm_alerts=True,
            min_risk_level="MEDIUM",
            alert_radius_km=100,
            max_daily_alerts=10,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            enable_push=True,
            enable_email=False,
            enable_sms=False,
            updated_at=datetime.utcnow()
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return {
        "user_id": preferences.user_id,
        "hurricane_alerts": preferences.hurricane_alerts,
        "heat_wave_alerts": preferences.heat_wave_alerts,
        "flood_alerts": preferences.flood_alerts,
        "severe_storm_alerts": preferences.severe_storm_alerts,
        "min_risk_level": preferences.min_risk_level,
        "alert_radius_km": preferences.alert_radius_km,
        "max_daily_alerts": preferences.max_daily_alerts,
        "quiet_hours_start": preferences.quiet_hours_start,
        "quiet_hours_end": preferences.quiet_hours_end,
        "enable_push": preferences.enable_push,
        "enable_email": preferences.enable_email,
        "enable_sms": preferences.enable_sms,
        "updated_at": preferences.updated_at,
    }


@router.put(
    "/{user_id}/preferences",
    response_model=dict,
    summary="Update user preferences",
    description="Update user disaster alert preferences"
)
async def update_preferences(
    user_id: str,
    preferences_update: UserPreferenceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update user alert preferences
    
    **Path Parameters:**
    - user_id: str - User unique identifier
    
    **Request Body:**
    - hurricane_alerts: Optional[bool]
    - heat_wave_alerts: Optional[bool]
    - flood_alerts: Optional[bool]
    - severe_storm_alerts: Optional[bool]
    - min_risk_level: Optional[str] - LOW, MEDIUM, HIGH, CRITICAL
    - alert_radius_km: Optional[int] - 10-500 km
    - max_daily_alerts: Optional[int] - 1-100
    - quiet_hours_start: Optional[str] - HH:MM format
    - quiet_hours_end: Optional[str] - HH:MM format
    - enable_push: Optional[bool]
    - enable_email: Optional[bool]
    - enable_sms: Optional[bool]
    
    **Security:**
    - Requires valid JWT token
    - Can only update own preferences
    
    **Returns:**
    - Updated preferences
    """
    
    # Verify access
    if current_user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other user's preferences"
        )
    
    # Get existing preferences or create new ones
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)
    
    # Update fields if provided
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(preferences, field):
            setattr(preferences, field, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)
    
    return {
        "user_id": preferences.user_id,
        "hurricane_alerts": preferences.hurricane_alerts,
        "heat_wave_alerts": preferences.heat_wave_alerts,
        "flood_alerts": preferences.flood_alerts,
        "severe_storm_alerts": preferences.severe_storm_alerts,
        "min_risk_level": preferences.min_risk_level,
        "alert_radius_km": preferences.alert_radius_km,
        "max_daily_alerts": preferences.max_daily_alerts,
        "quiet_hours_start": preferences.quiet_hours_start,
        "quiet_hours_end": preferences.quiet_hours_end,
        "enable_push": preferences.enable_push,
        "enable_email": preferences.enable_email,
        "enable_sms": preferences.enable_sms,
        "updated_at": preferences.updated_at,
    }
