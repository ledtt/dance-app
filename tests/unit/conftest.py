# tests/unit/conftest.py

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Set test environment variables before importing any modules
def setup_test_environment():
    """Set up test environment variables"""
    # Set minimal required environment variables for testing
    os.environ.update({
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
        "JWT_SECRET": "test-jwt-secret-key-that-is-long-enough-for-validation",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "SQLALCHEMY_ECHO": "false",
        "DEBUG": "true",
        "CORS_ORIGINS": '["http://localhost:3000"]',
        "ALLOWED_HOSTS": '["localhost", "127.0.0.1"]',
        "RATE_LIMIT_LOGIN": "5/minute",
        "RATE_LIMIT_REGISTER": "3/minute",
        "INTERNAL_AUTH_TOKEN": "internal-secret-token",
        "SERVICE_TOKEN_EXPIRE_MINUTES": "5",
        "SERVICE_JWT_SECRET": "test-service-jwt-secret-key-that-is-long-enough",
        "ADMIN_EMAIL": "admin@test.com",
        "ADMIN_PASSWORD": "test-admin-password",
        "AUTO_CREATE_ADMIN": "true",
        "SCHEDULE_SERVICE_URL": "http://localhost:8002",
        "AUTH_SERVICE_URL": "http://localhost:8001",
        "TESTING": "true"
    })

# Call setup before any imports
setup_test_environment()

# Mock all database and external dependencies at module level
@pytest.fixture(autouse=True, scope="session")
def mock_all_dependencies():
    """Mock all external dependencies for the entire test session"""
    
    # Mock database engines and sessions
    mock_engine = MagicMock()
    mock_session = MagicMock()
    
    with patch('sqlalchemy.ext.asyncio.create_async_engine', return_value=mock_engine), \
         patch('sqlalchemy.ext.asyncio.async_sessionmaker', return_value=MagicMock(return_value=mock_session)), \
         patch('services.auth.src.db.get_db', return_value=mock_session), \
         patch('services.booking.src.db.get_db', return_value=mock_session), \
         patch('services.schedule.src.db.get_db', return_value=mock_session), \
         patch('services.auth.src.db.engine', mock_engine), \
         patch('services.booking.src.db.engine', mock_engine), \
         patch('services.schedule.src.db.engine', mock_engine):
        
        yield {
            'engine': mock_engine,
            'session': mock_session
        }

@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external service calls for all tests"""
    with patch('services.booking.src.external_schedule.get_class_template_by_id') as mock_get_class, \
         patch('services.booking.src.external_schedule.get_user_by_id') as mock_get_user, \
         patch('services.booking.src.external_schedule.get_class_ids_by_filter') as mock_get_classes, \
         patch('httpx.AsyncClient.get') as mock_http_get, \
         patch('httpx.AsyncClient.post') as mock_http_post:
        
        # Set default return values
        mock_get_class.return_value = {
            "id": "test-class-id",
            "name": "Test Class",
            "teacher": "Test Teacher",
            "weekday": 1,
            "start_time": "10:00",
            "capacity": 10
        }
        mock_get_user.return_value = {
            "id": "test-user-id",
            "name": "Test User",
            "email": "test@example.com"
        }
        mock_get_classes.return_value = ["test-class-id"]
        
        # Mock HTTP responses
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.status_code = 200
        mock_http_get.return_value = mock_response
        mock_http_post.return_value = mock_response
        
        yield {
            'get_class_template_by_id': mock_get_class,
            'get_user_by_id': mock_get_user,
            'get_class_ids_by_filter': mock_get_classes,
            'http_get': mock_http_get,
            'http_post': mock_http_post
        }
