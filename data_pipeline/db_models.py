"""
Database Models for StormGuard
================================
SQLAlchemy ORM models for PostgreSQL
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, List, Enum, ForeignKey, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class User(Base):
    """User model for StormGuard platform"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    city = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    # Preferences
    interests = Column(String(500), default="hurricane,heat_wave,flood")  # Comma-separated
    notification_enabled = Column(Boolean, default=True)
    notification_token = Column(String(500), nullable=True)  # FCM token
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, city={self.city})>"


class DisasterType(str, enum.Enum):
    """Types of disasters"""
    HURRICANE = "hurricane"
    HEAT_WAVE = "heat_wave"
    FLOOD = "flood"
    SEVERE_STORM = "severe_storm"
    TORNADO = "tornado"
    WILDFIRE = "wildfire"


class Alert(Base):
    """Alert model - notifications sent to users"""
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Alert content
    disaster_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, nullable=False)  # 0-1
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Integer, default=100)
    
    # Status
    sent = Column(Boolean, default=False)
    read = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, user={self.user_id}, type={self.disaster_type})>"


class ChatMessage(Base):
    """Chat history model"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Message content
    user_message = Column(String(2000), nullable=False)
    assistant_response = Column(String(4000), nullable=False)
    sources = Column(String(2000), nullable=True)  # JSON array of sources used
    
    # Metadata
    session_id = Column(String(36), nullable=True, index=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, user={self.user_id})>"


class UserPreference(Base):
    """User preferences for notifications"""
    __tablename__ = "user_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Notification settings
    hurricane_alerts = Column(Boolean, default=True)
    heat_wave_alerts = Column(Boolean, default=True)
    flood_alerts = Column(Boolean, default=True)
    severe_storm_alerts = Column(Boolean, default=True)
    
    # Thresholds
    min_risk_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    alert_radius_km = Column(Integer, default=100)
    
    # Frequency
    max_daily_alerts = Column(Integer, default=10)
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # "08:00"
    
    # Channels
    enable_push = Column(Boolean, default=True)
    enable_email = Column(Boolean, default=True)
    enable_sms = Column(Boolean, default=False)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"
