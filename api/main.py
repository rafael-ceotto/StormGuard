"""
StormGuard AI - FastAPI Application
====================================
High-performance inference API for disaster predictions.

Features:
- Real-time predictions with confidence intervals
- Caching with Redis
- Comprehensive logging
- Health checks
- Prometheus metrics
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import os

# Import routers
from api.routers import predictions, health, models, auth, users

# Setup logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="StormGuard AI",
    description="Real-time Disaster Prediction Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(users.router, tags=["users"])
app.include_router(predictions.router, prefix="/api/v1", tags=["predictions"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "StormGuard AI",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("StormGuard AI API starting up")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("StormGuard AI API shutting down")

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        workers=int(os.getenv("API_WORKERS", 4)),
    )
