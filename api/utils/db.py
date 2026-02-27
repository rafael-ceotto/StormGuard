"""
Database Connection and Session Management
==========================================
SQLAlchemy engine and session setup
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from api.config import get_settings


settings = get_settings()

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.API_DEBUG,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Session:
    """
    Dependency for getting DB session
    
    Yields:
        SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
