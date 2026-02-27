"""
Authentication Router for StormGuard API
========================================
User registration and login endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.schemas.user import UserRegister, UserResponse
from api.utils.auth import hash_password, verify_password, create_user_token
from api.utils.db import get_db
from data_pipeline.db_models import User
import uuid
from datetime import datetime


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"]
)


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with location and disaster interests"
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    **Request Body:**
    - email: EmailStr - User email (must be unique)
    - full_name: str - Full name
    - latitude: float - Geographic latitude (-90 to 90)
    - longitude: float - Geographic longitude (-180 to 180)
    - city: Optional[str] - City name
    - country: Optional[str] - Country name
    - timezone: str - IANA timezone (default: UTC)
    - interests: List[str] - Disaster types to monitor
    
    **Returns:**
    - user: UserResponse - Created user data
    - access_token: str - JWT token for authentication
    - token_type: str - "bearer"
    """
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {user_data.email} already exists"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    new_user = User(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        latitude=user_data.latitude,
        longitude=user_data.longitude,
        city=user_data.city,
        country=user_data.country,
        timezone=user_data.timezone,
        interests=",".join(user_data.interests),
        notification_enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    access_token = create_user_token(user_id=user_id, email=user_data.email)
    
    return {
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "latitude": new_user.latitude,
            "longitude": new_user.longitude,
            "city": new_user.city,
            "country": new_user.country,
            "timezone": new_user.timezone,
            "interests": new_user.interests,
            "notification_enabled": new_user.notification_enabled,
            "created_at": new_user.created_at,
            "updated_at": new_user.updated_at,
            "last_login": new_user.last_login,
        },
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post(
    "/login",
    response_model=dict,
    summary="Login user",
    description="Authenticate user and receive JWT token"
)
async def login(
    email: str,
    password: str = None,
    db: Session = Depends(get_db)
):
    """
    Login a user
    
    **Note:** Current implementation (Phase 1) uses email-based authentication only.
    Phase 2 will add password-based authentication.
    
    **Request Parameters:**
    - email: str - User email
    - password: Optional[str] - Password (optional for Phase 1)
    
    **Returns:**
    - user: UserResponse - User data
    - access_token: str - JWT token for authentication
    - token_type: str - "bearer"
    """
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Generate token
    access_token = create_user_token(user_id=user.id, email=user.email)
    
    return {
        "user": {
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
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
        },
        "access_token": access_token,
        "token_type": "bearer"
    }
