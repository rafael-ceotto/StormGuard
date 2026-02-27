"""
Alerts Router for StormGuard API
================================
Disaster alert management and notification endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from api.utils.auth import get_current_user
from api.utils.db import get_db
from api.services.notification_service import get_notification_service, NotificationService
from data_pipeline.db_models import Alert, User, UserPreference
import uuid


router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["alerts"]
)


# ===== Pydantic Models =====

class AlertCreate(BaseModel):
    """Alert creation request"""
    disaster_type: str
    title: str
    message: str
    risk_level: str
    risk_score: float
    latitude: float
    longitude: float
    radius_km: int = 100


class AlertResponse(BaseModel):
    """Alert response model"""
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


class SendAlertRequest(BaseModel):
    """Request to send alert to users"""
    user_ids: List[str]
    disaster_type: str
    title: str
    message: str
    risk_level: str
    risk_score: float
    latitude: float
    longitude: float
    radius_km: int = 100


class AlertStatsResponse(BaseModel):
    """Alert statistics response"""
    total_alerts: int
    sent: int
    read: int
    clicked: int
    by_type: dict


# ===== Endpoints =====

@router.get(
    "/user/{user_id}",
    response_model=List[AlertResponse],
    summary="Get user alerts",
    description="Retrieve all alerts for a user"
)
async def get_user_alerts(
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[AlertResponse]:
    """
    Get alerts for a user
    
    **Path Parameters:**
    - user_id: str - User ID
    
    **Query Parameters:**
    - limit: int - Maximum number of alerts to return (default: 100)
    - offset: int - Offset for pagination (default: 0)
    - unread_only: bool - Only return unread alerts (default: false)
    
    **Security:**
    - Requires valid JWT token
    - Can only access own alerts
    
    **Returns:**
    - List of AlertResponse objects
    """
    
    # Verify access
    if current_user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's alerts"
        )
    
    # Build query
    query = db.query(Alert).filter(Alert.user_id == user_id)
    
    if unread_only:
        query = query.filter(Alert.read == False)
    
    # Order by created_at descending and apply pagination
    alerts = query.order_by(Alert.created_at.desc()).limit(
        limit
    ).offset(offset).all()
    
    return [AlertResponse.from_orm(alert) for alert in alerts]


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert details",
    description="Retrieve details of a specific alert"
)
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AlertResponse:
    """
    Get alert details
    
    **Path Parameters:**
    - alert_id: str - Alert ID
    
    **Security:**
    - Requires valid JWT token
    - Can only access own alerts
    """
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    # Verify access
    if current_user.get("sub") != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's alerts"
        )
    
    return AlertResponse.from_orm(alert)


@router.post(
    "/{alert_id}/read",
    response_model=AlertResponse,
    summary="Mark alert as read",
    description="Mark an alert as read"
)
async def mark_alert_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AlertResponse:
    """
    Mark alert as read
    
    **Path Parameters:**
    - alert_id: str - Alert ID
    
    **Security:**
    - Requires valid JWT token
    """
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    # Verify access
    if current_user.get("sub") != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other user's alerts"
        )
    
    alert.read = True
    alert.read_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    
    return AlertResponse.from_orm(alert)


@router.post(
    "/{alert_id}/click",
    response_model=AlertResponse,
    summary="Record alert click",
    description="Record user click on alert (for engagement tracking)"
)
async def record_alert_click(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AlertResponse:
    """
    Record alert click
    
    **Path Parameters:**
    - alert_id: str - Alert ID
    
    **Returns:**
    - Updated alert with clicked=true
    """
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    # Verify access
    if current_user.get("sub") != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other user's alerts"
        )
    
    alert.clicked = True
    alert.read = True
    alert.read_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    
    return AlertResponse.from_orm(alert)


@router.post(
    "/send",
    response_model=dict,
    summary="Send alert to users",
    description="Trigger alert to be sent to specified users via push notification"
)
async def send_alert(
    request: SendAlertRequest,
    db: Session = Depends(get_db),
    notification_service: NotificationService = Depends(get_notification_service)
) -> dict:
    """
    Send alert to users
    
    **Request Body:**
    - user_ids: List[str] - User IDs to send alert to
    - disaster_type: str - Type of disaster
    - title: str - Alert title
    - message: str - Alert message
    - risk_level: str - Risk severity
    - risk_score: float - Risk score 0-1
    - latitude: float - Alert latitude
    - longitude: float - Alert longitude
    - radius_km: int - Impact radius in kilometers
    
    **Returns:**
    - Summary of send results
    """
    
    alert_data = {
        "disaster_type": request.disaster_type,
        "title": request.title,
        "message": request.message,
        "risk_level": request.risk_level,
        "risk_score": request.risk_score,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "location": f"({request.latitude}, {request.longitude})",
        "radius_km": request.radius_km
    }
    
    # Send to all users
    results = await notification_service.send_bulk_alerts(
        users=request.user_ids,
        alert_data=alert_data,
        db=db
    )
    
    return results


@router.get(
    "/stats/{user_id}",
    response_model=AlertStatsResponse,
    summary="Get alert statistics",
    description="Get alert statistics for a user"
)
async def get_alert_stats(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AlertStatsResponse:
    """
    Get alert statistics
    
    **Path Parameters:**
    - user_id: str - User ID
    
    **Security:**
    - Requires valid JWT token
    - Can only access own stats
    
    **Returns:**
    - Alert statistics including counts by type
    """
    
    # Verify access
    if current_user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's stats"
        )
    
    alerts = db.query(Alert).filter(Alert.user_id == user_id).all()
    
    if not alerts:
        return AlertStatsResponse(
            total_alerts=0,
            sent=0,
            read=0,
            clicked=0,
            by_type={}
        )
    
    # Calculate statistics
    by_type = {}
    read_count = 0
    clicked_count = 0
    
    for alert in alerts:
        # Count by type
        dtype = alert.disaster_type
        if dtype not in by_type:
            by_type[dtype] = 0
        by_type[dtype] += 1
        
        # Count read and clicked
        if alert.read:
            read_count += 1
        if alert.clicked:
            clicked_count += 1
    
    return AlertStatsResponse(
        total_alerts=len(alerts),
        sent=sum(1 for a in alerts if a.sent),
        read=read_count,
        clicked=clicked_count,
        by_type=by_type
    )


@router.delete(
    "/{alert_id}",
    summary="Delete alert",
    description="Delete an alert"
)
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Delete an alert
    
    **Path Parameters:**
    - alert_id: str - Alert ID to delete
    
    **Security:**
    - Requires valid JWT token
    - Can only delete own alerts
    """
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    # Verify access
    if current_user.get("sub") != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other user's alerts"
        )
    
    db.delete(alert)
    db.commit()
    
    return {
        "deleted": True,
        "alert_id": alert_id,
        "message": f"Alert {alert_id} deleted"
    }
