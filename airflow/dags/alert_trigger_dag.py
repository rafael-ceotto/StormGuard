"""
Alert Trigger DAG - Integration with StormGuard API
====================================================
Monitors predictions and sends alerts to users via Firebase FCM.

Triggered after realtime inference completes.
Sends alerts to users at risk in affected areas.

Frequency: Every 6 hours (after inference)
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.models import Variable
import logging
import requests
import json
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'stormguard-alerts',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

# Configuration
API_BASE_URL = Variable.get("STORMGUARD_API_URL", "http://localhost:8000")
API_KEY = Variable.get("STORMGUARD_API_KEY", "")
RISK_THRESHOLD = float(Variable.get("ALERT_RISK_THRESHOLD", 0.60))  # 60% risk = send alert


@dag(
    dag_id='stormguard_alert_trigger',
    default_args=default_args,
    description='Alert trigger pipeline - sends notifications for disasters',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['alerts', 'notifications', 'integration'],
)
def stormguard_alert_trigger():
    """
    Main alert trigger DAG
    
    Flow:
    1. Get latest predictions from database
    2. Identify affected areas and disaster types
    3. Query users in affected areas
    4. Filter by user preferences
    5. Send alerts via Firebase FCM
    6. Record alert status in database
    """

    @task
    def get_latest_predictions(**context) -> Dict:
        """
        Get latest disaster predictions from database
        
        Returns predictions with:
        - disaster_type (hurricane, flood, heat_wave, tornado, etc.)
        - risk_score (0-1)
        - latitude, longitude (prediction location)
        - radius_km (affected area radius)
        - timestamp
        """
        from sqlalchemy import create_engine, text
        from api.config import get_settings
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        logger.info("Fetching latest predictions from database")
        
        try:
            with engine.connect() as conn:
                # Query latest predictions
                # This assumes predictions are stored in a table
                # Adjust query based on your actual schema
                query = text("""
                    SELECT 
                        disaster_type,
                        risk_score,
                        latitude,
                        longitude,
                        affected_radius_km,
                        created_at,
                        prediction_id
                    FROM predictions
                    WHERE created_at >= NOW() - INTERVAL '6 hours'
                    AND risk_score > :risk_threshold
                    ORDER BY created_at DESC, risk_score DESC
                """)
                
                result = conn.execute(query, {"risk_threshold": RISK_THRESHOLD})
                predictions = [dict(row._mapping) for row in result]
                
                logger.info(f"Found {len(predictions)} high-risk predictions")
                
                if not predictions:
                    logger.warning("No predictions above risk threshold")
                    return {"predictions": [], "count": 0}
                
                return {
                    "predictions": predictions,
                    "count": len(predictions),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error fetching predictions: {e}")
            raise

    @task
    def identify_affected_users(predictions_data: Dict) -> Dict:
        """
        Identify users in affected areas based on predictions
        
        For each prediction:
        - Find users within the affected radius
        - Match disaster type with user interests
        - Apply user preference filters
        
        Returns list of users to alert with risk details
        """
        from sqlalchemy import create_engine, text
        from api.config import get_settings
        from math import radians, cos, sin, asin, sqrt
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        logger.info("Identifying affected users")
        
        if not predictions_data.get("predictions"):
            return {"alerts_to_send": [], "count": 0}
        
        alerts_to_send = []
        
        try:
            with engine.connect() as conn:
                for prediction in predictions_data["predictions"]:
                    disaster_type = prediction["disaster_type"]
                    risk_score = prediction["risk_score"]
                    pred_lat = prediction["latitude"]
                    pred_lon = prediction["longitude"]
                    radius_km = prediction.get("affected_radius_km", 100)
                    
                    logger.info(
                        f"Processing prediction: {disaster_type} "
                        f"({risk_score:.2%} risk) at ({pred_lat}, {pred_lon})"
                    )
                    
                    # Query users in affected area with matching interests
                    query = text("""
                        SELECT DISTINCT
                            u.id,
                            u.email,
                            u.full_name,
                            u.latitude,
                            u.longitude,
                            u.notification_token,
                            u.notification_enabled,
                            up.user_id as has_preferences,
                            up.min_risk_level,
                            up.alert_radius_km
                        FROM users u
                        LEFT JOIN user_preferences up ON u.id = up.user_id
                        WHERE u.notification_enabled = true
                        AND u.notification_token IS NOT NULL
                        AND (
                            -- Check if user has this disaster type enabled
                            (:disaster_type = 'hurricane' AND COALESCE(up.hurricane_alerts, true))
                            OR (:disaster_type = 'heat_wave' AND COALESCE(up.heat_wave_alerts, true))
                            OR (:disaster_type = 'flood' AND COALESCE(up.flood_alerts, true))
                            OR (:disaster_type = 'severe_storm' AND COALESCE(up.severe_storm_alerts, true))
                            OR (:disaster_type = 'tornado' AND COALESCE(up.severe_storm_alerts, true))
                            OR (:disaster_type = 'wildfire' AND COALESCE(up.severe_storm_alerts, true))
                        )
                        -- Approximate distance calculation (haversine)
                        -- For simplicity, use lat/lon bounding box
                        AND u.latitude BETWEEN :lat_min AND :lat_max
                        AND u.longitude BETWEEN :lon_min AND :lon_max
                    """)
                    
                    # Calculate bounding box (rough approximation: 1 degree ≈ 111 km)
                    lat_offset = radius_km / 111.0
                    lon_offset = radius_km / (111.0 * cos(radians(pred_lat)))
                    
                    params = {
                        "disaster_type": disaster_type,
                        "lat_min": pred_lat - lat_offset,
                        "lat_max": pred_lat + lat_offset,
                        "lon_min": pred_lon - lon_offset,
                        "lon_max": pred_lon + lon_offset,
                    }
                    
                    result = conn.execute(query, params)
                    affected_users = [dict(row._mapping) for row in result]
                    
                    logger.info(f"Found {len(affected_users)} users affected by {disaster_type}")
                    
                    # Create alert for each user
                    for user in affected_users:
                        # Check risk level preference
                        min_risk_level = user.get("min_risk_level", "MEDIUM")
                        risk_threshold_map = {
                            "LOW": 0.30,
                            "MEDIUM": 0.60,
                            "HIGH": 0.80,
                            "CRITICAL": 0.95
                        }
                        
                        if risk_score >= risk_threshold_map.get(min_risk_level, 0.60):
                            alerts_to_send.append({
                                "user_id": user["id"],
                                "email": user["email"],
                                "full_name": user["full_name"],
                                "notification_token": user["notification_token"],
                                "disaster_type": disaster_type,
                                "risk_score": risk_score,
                                "latitude": pred_lat,
                                "longitude": pred_lon,
                                "radius_km": radius_km,
                                "user_location": (user["latitude"], user["longitude"]),
                            })
        
        except Exception as e:
            logger.error(f"Error identifying affected users: {e}")
            raise
        
        logger.info(f"Total alerts to send: {len(alerts_to_send)}")
        
        return {
            "alerts_to_send": alerts_to_send,
            "count": len(alerts_to_send)
        }

    @task
    def send_alerts(alerts_data: Dict) -> Dict:
        """
        Send alerts to users via Firebase FCM
        
        Makes HTTP requests to the StormGuard API alert endpoint
        """
        logger.info(f"Sending {alerts_data['count']} alerts")
        
        if not alerts_data.get("alerts_to_send"):
            logger.info("No alerts to send")
            return {"sent": 0, "failed": 0, "errors": []}
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Prepare bulk alert request
            user_ids = [alert["user_id"] for alert in alerts_data["alerts_to_send"]]
            
            # Get first alert for disaster type details
            first_alert = alerts_data["alerts_to_send"][0]
            
            alert_request = {
                "user_ids": user_ids,
                "disaster_type": first_alert["disaster_type"],
                "title": f"{first_alert['disaster_type'].title()} Alert",
                "message": f"⚠️ {first_alert['disaster_type'].title()} risk detected in your area. "
                          f"Risk level: {_get_risk_level(first_alert['risk_score'])}",
                "risk_level": _get_risk_level(first_alert["risk_score"]),
                "risk_score": first_alert["risk_score"],
                "latitude": first_alert["latitude"],
                "longitude": first_alert["longitude"],
                "radius_km": first_alert["radius_km"],
            }
            
            logger.info(f"Sending bulk alert request: {json.dumps(alert_request, indent=2)}")
            
            # Send to API
            response = requests.post(
                f"{API_BASE_URL}/api/v1/alerts/send",
                json=alert_request,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"bearer {API_KEY}" if API_KEY else ""
                },
                timeout=30
            )
            
            logger.info(f"API response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                sent_count = result.get("sent", 0)
                failed_count = result.get("failed", 0)
                errors = result.get("errors", [])
                
                logger.info(
                    f"Alert send result: {sent_count} sent, "
                    f"{failed_count} failed"
                )
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                errors.append(error_msg)
                failed_count = len(user_ids)
        
        except Exception as e:
            logger.error(f"Error sending alerts: {e}")
            errors.append(str(e))
            failed_count = len(alerts_data.get("alerts_to_send", []))
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "errors": errors
        }

    @task
    def record_alert_status(send_result: Dict) -> Dict:
        """
        Record alert send status in database for metrics/reporting
        """
        from sqlalchemy import create_engine, text
        from api.config import get_settings
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        logger.info("Recording alert send status")
        
        try:
            with engine.connect() as conn:
                # Record metrics
                query = text("""
                    INSERT INTO alert_metrics (
                        timestamp,
                        total_sent,
                        total_failed,
                        created_at
                    ) VALUES (
                        :timestamp,
                        :sent,
                        :failed,
                        NOW()
                    )
                """)
                
                conn.execute(query, {
                    "timestamp": datetime.utcnow(),
                    "sent": send_result["sent"],
                    "failed": send_result["failed"]
                })
                conn.commit()
                
                logger.info(
                    f"Recorded metrics: {send_result['sent']} sent, "
                    f"{send_result['failed']} failed"
                )
        
        except Exception as e:
            # This is non-critical, just log the error
            logger.warning(f"Error recording alert metrics: {e}")
        
        return {
            "status": "recorded",
            "summary": send_result
        }

    @task
    def generate_report(**context) -> Dict:
        """
        Generate execution report
        """
        ti = context['task_instance']
        
        predictions = ti.xcom_pull(
            task_ids='get_latest_predictions'
        )
        affected_users_data = ti.xcom_pull(
            task_ids='identify_affected_users'
        )
        send_result = ti.xcom_pull(
            task_ids='send_alerts'
        )
        
        report = {
            "execution_time": datetime.utcnow().isoformat(),
            "predictions_found": predictions.get("count", 0),
            "users_affected": affected_users_data.get("count", 0),
            "alerts_sent": send_result.get("sent", 0),
            "alerts_failed": send_result.get("failed", 0),
            "errors": send_result.get("errors", [])
        }
        
        logger.info(f"Alert trigger DAG completed: {json.dumps(report, indent=2)}")
        
        return report

    # Task dependencies
    predictions = get_latest_predictions()
    affected_users = identify_affected_users(predictions)
    send_result = send_alerts(affected_users)
    record_status = record_alert_status(send_result)
    report = generate_report()
    
    # Set dependencies
    predictions >> affected_users >> send_result >> record_status
    [record_status, send_result] >> report


# Instantiate DAG
alert_trigger_dag = stormguard_alert_trigger()


# ===== Helper Functions =====

def _get_risk_level(risk_score: float) -> str:
    """Convert risk score to risk level"""
    if risk_score >= 0.95:
        return "CRITICAL"
    elif risk_score >= 0.80:
        return "HIGH"
    elif risk_score >= 0.60:
        return "MEDIUM"
    else:
        return "LOW"
