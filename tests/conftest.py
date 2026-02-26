"""
pytest configuration
"""

import pytest
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory"""
    return PROJECT_ROOT / "tests" / "data"

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        "latitude": 25.7617,
        "longitude": -80.1918,
        "temperature": 28.5,
        "humidity": 75.0,
        "pressure": 1010.25,
        "wind_speed": 12.5,
        "wind_direction": 200,
        "precipitation": 0.5,
    }
