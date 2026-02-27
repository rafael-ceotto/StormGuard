"""
Configuration Module for StormGuard API
========================================
Centralized configuration for FastAPI application
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ===== API CONFIG =====
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "False").lower() == "true"
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    
    # ===== DATABASE CONFIG =====
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://airflow:airflow@postgres:5432/airflow"
    )
    
    # ===== JWT CONFIG =====
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "change-me-in-production-your-secret-key-here-min-32-chars"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # ===== LOGGING =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ===== REDIS =====
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # ===== FIREBASE CONFIG (for push notifications) =====
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        "/app/firebase-credentials.json"
    )
    
    # ===== PINECONE CONFIG (for RAG) =====
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "production")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "stormguard-rag")
    
    # ===== OPENAI CONFIG =====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
