"""
Firebase Push Notification Service for StormGuard API
=====================================================
Real-time disaster alerts via FCM (Firebase Cloud Messaging)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, messaging
from api.config import get_settings
from sqlalchemy.orm import Session
from data_pipeline.db_models import User, Alert, UserPreference
import os


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Firebase Cloud Messaging (FCM) notification service
    
    Sends push notifications to user devices about disaster alerts
    """
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self.settings = get_settings()
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if len(firebase_admin._apps) > 0:
                self.app = firebase_admin._apps.get('default')
                logger.info("✓ Firebase already initialized")
                return
            
            # Check if credentials file exists
            creds_path = self.settings.FIREBASE_CREDENTIALS_PATH
            
            if not os.path.exists(creds_path):
                logger.warning(f"Firebase credentials not found at {creds_path}")
                logger.warning("Push notifications will not be available")
                self.app = None
                return
            
            # Initialize with credentials
            cred = credentials.Certificate(creds_path)
            self.app = firebase_admin.initialize_app(cred)
            
            logger.info("✓ Firebase Admin SDK initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            logger.warning("Push notifications will not be available")
            self.app = None
    
    async def send_alert(
        self,
        user_id: str,
        alert_data: Dict,
        db: Session
    ) -> Dict:
        """
        Send disaster alert to user via push notification
        
        Args:
            user_id: User ID to send alert to
            alert_data: Alert data (disaster_type, risk_score, location, etc.)
            db: Database session
            
        Returns:
            Result dict with success status and message ID
        """
        
        if not self.app:
            return {
                "success": False,
                "error": "Firebase not initialized"
            }
        
        try:
            # Get user and preferences
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.notification_token:
                return {
                    "success": False,
                    "error": "User or device token not found"
                }
            
            preferences = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()
            
            # Check if notifications are enabled for this disaster type
            if not self._should_send_notification(alert_data, preferences):
                return {
                    "success": False,
                    "skipped": True,
                    "reason": "Alert disabled in user preferences"
                }
            
            # Create notification message
            notification = self._create_notification(alert_data)
            
            # Send message via FCM
            response = messaging.send(
                messaging.Message(
                    notification=notification["notification"],
                    data=notification["data"],
                    token=user.notification_token,
                )
            )
            
            # Create alert record in database
            self._create_alert_record(
                user_id=user_id,
                alert_data=alert_data,
                db=db
            )
            
            logger.info(f"Alert sent to user {user_id}: {response}")
            
            return {
                "success": True,
                "message_id": response,
                "user_id": user_id
            }
        
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_alerts(
        self,
        users: List[str],
        alert_data: Dict,
        db: Session
    ) -> Dict:
        """
        Send alert to multiple users
        
        Args:
            users: List of user IDs
            alert_data: Alert data
            db: Database session
            
        Returns:
            Summary of send results
        """
        
        results = {
            "total": len(users),
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        for user_id in users:
            result = await self.send_alert(user_id, alert_data, db)
            
            if result["success"]:
                results["sent"] += 1
            elif result.get("skipped"):
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user_id,
                    "error": result.get("error", "Unknown error")
                })
        
        return results
    
    def _should_send_notification(
        self,
        alert_data: Dict,
        preferences: Optional[object]
    ) -> bool:
        """Check if notification should be sent based on preferences"""
        
        if not preferences:
            return True
        
        disaster_type = alert_data.get("disaster_type", "").lower()
        risk_score = alert_data.get("risk_score", 0)
        
        # Check if this disaster type is enabled
        type_map = {
            "hurricane": "hurricane_alerts",
            "heat_wave": "heat_wave_alerts",
            "flood": "flood_alerts",
            "severe_storm": "severe_storm_alerts",
            "tornado": "severe_storm_alerts",
            "wildfire": "severe_storm_alerts"
        }
        
        pref_field = type_map.get(disaster_type)
        if pref_field and not getattr(preferences, pref_field, True):
            return False
        
        # Check risk level threshold
        min_risk = {
            "LOW": 0.3,
            "MEDIUM": 0.6,
            "HIGH": 0.8,
            "CRITICAL": 0.9
        }
        
        threshold = min_risk.get(
            preferences.min_risk_level,
            0.6
        )
        
        if risk_score < threshold:
            return False
        
        return True
    
    def _create_notification(self, alert_data: Dict) -> Dict:
        """Create FCM notification message"""
        
        disaster_type = alert_data.get("disaster_type", "Disaster")
        risk_score = alert_data.get("risk_score", 0)
        location = alert_data.get("location", "Unknown location")
        
        # Determine risk level and emoji
        if risk_score >= 0.9:
            risk_level = "CRITICAL"
            emoji = "🚨"
        elif risk_score >= 0.8:
            risk_level = "HIGH"
            emoji = "⚠️"
        elif risk_score >= 0.6:
            risk_level = "MEDIUM"
            emoji = "⚠️"
        else:
            risk_level = "LOW"
            emoji = "ℹ️"
        
        title = f"{emoji} {disaster_type.title()} Alert"
        body = f"{risk_level} risk in {location}"
        
        return {
            "notification": messaging.Notification(
                title=title,
                body=body,
                image=self._get_alert_icon(disaster_type)
            ),
            "data": {
                "alert_type": disaster_type,
                "risk_level": risk_level,
                "risk_score": str(risk_score),
                "location": location,
                "timestamp": datetime.utcnow().isoformat(),
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            }
        }
    
    def _get_alert_icon(self, disaster_type: str) -> str:
        """Get icon URL for disaster type"""
        
        icon_urls = {
            "hurricane": "https://example.com/icons/hurricane.png",
            "heat_wave": "https://example.com/icons/heat-wave.png",
            "flood": "https://example.com/icons/flood.png",
            "severe_storm": "https://example.com/icons/storm.png",
            "tornado": "https://example.com/icons/tornado.png",
            "wildfire": "https://example.com/icons/wildfire.png"
        }
        
        return icon_urls.get(
            disaster_type.lower(),
            "https://example.com/icons/default.png"
        )
    
    def _create_alert_record(
        self,
        user_id: str,
        alert_data: Dict,
        db: Session
    ) -> None:
        """Create alert record in database"""
        
        from uuid import uuid4
        
        alert = Alert(
            id=str(uuid4()),
            user_id=user_id,
            disaster_type=alert_data.get("disaster_type"),
            title=alert_data.get("title"),
            message=alert_data.get("message"),
            risk_level=alert_data.get("risk_level"),
            risk_score=alert_data.get("risk_score"),
            latitude=alert_data.get("latitude"),
            longitude=alert_data.get("longitude"),
            radius_km=alert_data.get("radius_km", 100),
            sent=True,
            sent_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.add(alert)
        db.commit()


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create notification service singleton"""
    global _notification_service
    
    if _notification_service is None:
        _notification_service = NotificationService()
    
    return _notification_service
