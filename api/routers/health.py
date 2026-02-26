"""
Health Check Router
===================
Endpoints for monitoring API health.
"""

from fastapi import APIRouter
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "StormGuard API",
        "version": "1.0.0",
    }

@router.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    try:
        # Check dependencies
        deps_ok = True
        
        # In production: check database, cache, model load, etc
        
        if deps_ok:
            return {"ready": True}
        else:
            return {"ready": False}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {"ready": False, "error": str(e)}

@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"live": True}

@router.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    # In production: return proper Prometheus metrics
    return {
        "requests_total": 1000,
        "requests_failed": 5,
        "predictions_total": 950,
        "model_inference_time_ms": 45,
    }
