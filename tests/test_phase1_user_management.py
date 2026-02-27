"""
Tests for StormGuard Phase 1 - User Management API
===================================================
Test registration, login, and preference management endpoints
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.utils.db import SessionLocal
from data_pipeline.db_models import User, UserPreference
from sqlalchemy import delete


client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up test data after each test"""
    yield
    
    db = SessionLocal()
    try:
        db.execute(delete(UserPreference))
        db.execute(delete(User))
        db.commit()
    finally:
        db.close()


class TestRegistration:
    """Test user registration endpoint"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
            "timezone": "America/New_York",
            "interests": ["hurricane", "heat_wave"]
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert "token_type" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["token_type"] == "bearer"
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": "duplicate@example.com",
            "full_name": "Test User",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA"
        }
        
        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration with same email
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]
    
    def test_register_invalid_latitude(self):
        """Test registration with invalid latitude"""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "latitude": 100,  # Invalid: > 90
            "longitude": -74.0060,
            "city": "New York"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Test user login endpoint"""
    
    def test_login_success(self):
        """Test successful login"""
        # Register a user first
        user_data = {
            "email": "login@example.com",
            "full_name": "Login User",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Try to login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 401


class TestUserProfile:
    """Test user profile endpoints"""
    
    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a test user"""
        user_data = {
            "email": "profile@example.com",
            "full_name": "Profile User",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        data = response.json()
        
        return {
            "user_id": data["user"]["id"],
            "token": data["access_token"]
        }
    
    def test_get_user_profile(self, authenticated_user):
        """Test getting user profile"""
        headers = {"Authorization": f"bearer {authenticated_user['token']}"}
        
        response = client.get(
            f"/api/v1/users/{authenticated_user['user_id']}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["latitude"] == 40.7128
    
    def test_update_user_profile(self, authenticated_user):
        """Test updating user profile"""
        headers = {"Authorization": f"bearer {authenticated_user['token']}"}
        
        update_data = {
            "full_name": "Updated Name",
            "city": "Los Angeles",
            "timezone": "America/Los_Angeles"
        }
        
        response = client.put(
            f"/api/v1/users/{authenticated_user['user_id']}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["city"] == "Los Angeles"
    
    def test_access_other_user_profile_fails(self, authenticated_user):
        """Test that users cannot access other users' profiles"""
        # Register another user
        other_user_data = {
            "email": "other@example.com",
            "full_name": "Other User",
            "latitude": 30.0,
            "longitude": -90.0
        }
        
        other_response = client.post("/api/v1/auth/register", json=other_user_data)
        other_user_id = other_response.json()["user"]["id"]
        
        # Try to access other user with first user's token
        headers = {"Authorization": f"bearer {authenticated_user['token']}"}
        response = client.get(
            f"/api/v1/users/{other_user_id}",
            headers=headers
        )
        
        assert response.status_code == 403


class TestPreferences:
    """Test user preference endpoints"""
    
    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a test user"""
        user_data = {
            "email": "pref@example.com",
            "full_name": "Preference User",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        data = response.json()
        
        return {
            "user_id": data["user"]["id"],
            "token": data["access_token"]
        }
    
    def test_get_default_preferences(self, authenticated_user):
        """Test getting default preferences for new user"""
        headers = {"Authorization": f"bearer {authenticated_user['token']}"}
        
        response = client.get(
            f"/api/v1/users/{authenticated_user['user_id']}/preferences",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["hurricane_alerts"] is True
        assert data["heat_wave_alerts"] is True
        assert data["flood_alerts"] is True
        assert data["user_id"] == authenticated_user["user_id"]
    
    def test_update_preferences(self, authenticated_user):
        """Test updating user preferences"""
        headers = {"Authorization": f"bearer {authenticated_user['token']}"}
        
        update_data = {
            "hurricane_alerts": False,
            "heat_wave_alerts": True,
            "min_risk_level": "HIGH",
            "alert_radius_km": 200,
            "enable_email": True,
            "enable_sms": True
        }
        
        response = client.put(
            f"/api/v1/users/{authenticated_user['user_id']}/preferences",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["hurricane_alerts"] is False
        assert data["heat_wave_alerts"] is True
        assert data["min_risk_level"] == "HIGH"
        assert data["alert_radius_km"] == 200
        assert data["enable_email"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
