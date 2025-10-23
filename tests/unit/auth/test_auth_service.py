# tests/unit/auth/test_auth_service.py

import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

# Mock all database and external dependencies before importing
with patch('services.auth.src.db.get_db'), \
     patch('services.auth.src.db.engine'), \
     patch('sqlalchemy.ext.asyncio.create_async_engine'), \
     patch('sqlalchemy.ext.asyncio.async_sessionmaker'):
    
    from services.auth.src.models import User
    from services.auth.src.schemas import UserCreate, UserUpdate, UserRoleUpdate, PasswordChange
    from services.auth.src.crud import (
        create_user, 
        get_user_by_email, 
        update_user_role,
        update_user,
        get_admin_count,
        change_user_password,
    )
    from services.auth.src.auth import authenticate_user, create_access_token

# --- Unit Tests for crud.py ---

@pytest.mark.asyncio
async def test_create_user_success():
    """Test successful user creation."""
    mock_db = AsyncMock()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        password="SecurePassword123!"
    )
    
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    mock_db.add = Mock()

    new_user = await create_user(mock_db, user_data)

    assert new_user.email == user_data.email
    assert new_user.name == user_data.name
    assert new_user.password_hash != user_data.password.get_secret_value()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    """Test user creation failure due to duplicate email."""
    mock_db = AsyncMock()
    user_data = UserCreate(email="test@example.com", name="Test User", password="SecurePassword123!")
    
    # Simulate database integrity error
    mock_db.commit.side_effect = IntegrityError(None, None, None)
    mock_db.rollback.return_value = None
    mock_db.add = Mock()

    with pytest.raises(HTTPException) as exc_info:
        await create_user(mock_db, user_data)
    
    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail
    mock_db.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_user_role_success():
    """Test successfully updating a user's role to admin."""
    mock_db = AsyncMock()
    user_id = uuid4()
    
    mock_user = User(id=user_id, email="test@example.com", role="user")

    # Mock the return value of get_user_by_id
    with patch('services.auth.src.crud.get_user_by_id', return_value=mock_user):
        # Mock get_admin_count
        with patch('services.auth.src.crud.get_admin_count', return_value=2):
            updated_user = await update_user_role(mock_db, user_id, "admin")

            assert updated_user.role == "admin"
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_user_role_prevent_last_admin_demotion():
    """Test that demoting the last admin is prevented."""
    mock_db = AsyncMock()
    user_id = uuid4()
    
    mock_user = User(id=user_id, email="admin@example.com", role="admin")

    with patch('services.auth.src.crud.get_user_by_id', return_value=mock_user):
        # Mock get_admin_count to return 1
        with patch('services.auth.src.crud.get_admin_count', return_value=1):
            with pytest.raises(HTTPException) as exc_info:
                await update_user_role(mock_db, user_id, "user")
            
            assert exc_info.value.status_code == 400
            assert "last administrator" in exc_info.value.detail
            mock_db.commit.assert_not_called()

# --- Unit Tests for auth.py ---

@pytest.mark.asyncio
@patch('services.auth.src.auth.get_user_by_email')
@patch('services.auth.src.auth.verify_password')
async def test_authenticate_user_success(mock_verify_password, mock_get_user_by_email):
    """Test successful user authentication."""
    mock_db = AsyncMock()
    mock_user = User(
        email="test@example.com", 
        password_hash="hashed_password"
    )
    
    # Mock the async function to return the user directly
    mock_get_user_by_email.return_value = mock_user
    # Mock password verification to return True
    mock_verify_password.return_value = True

    authenticated_user = await authenticate_user(mock_db, "test@example.com", "password123")
    
    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"
    mock_get_user_by_email.assert_called_once_with(mock_db, "test@example.com")
    mock_verify_password.assert_called_once_with("password123", "hashed_password")

@pytest.mark.asyncio
@patch('services.auth.src.auth.get_user_by_email')
@patch('services.auth.src.auth.verify_password')
async def test_authenticate_user_wrong_password(mock_verify_password, mock_get_user_by_email):
    """Test authentication failure due to wrong password."""
    mock_db = AsyncMock()
    mock_user = User(
        email="test@example.com", 
        password_hash="hashed_password"
    )
    
    mock_get_user_by_email.return_value = mock_user
    # Mock password verification to return False
    mock_verify_password.return_value = False

    authenticated_user = await authenticate_user(mock_db, "test@example.com", "wrong_password")
    
    assert authenticated_user is None
    mock_get_user_by_email.assert_called_once_with(mock_db, "test@example.com")
    mock_verify_password.assert_called_once_with("wrong_password", "hashed_password")

@pytest.mark.asyncio
@patch('services.auth.src.auth.get_user_by_email')
async def test_authenticate_user_not_found(mock_get_user_by_email):
    """Test authentication failure due to user not found."""
    mock_db = AsyncMock()
    
    # Mock the async function to return None
    mock_get_user_by_email.return_value = None

    authenticated_user = await authenticate_user(mock_db, "notfound@example.com", "password123")
    
    assert authenticated_user is None
    mock_get_user_by_email.assert_called_once_with(mock_db, "notfound@example.com")

@patch('services.auth.src.auth.jwt_manager')
def test_create_access_token(mock_jwt_manager):
    """Test the structure and content of a created JWT."""
    user_id = str(uuid4())
    user_data = {
        "sub": user_id,
        "role": "admin",
        "name": "Test Admin"
    }
    
    # Mock the JWT manager's create_access_token method
    mock_jwt_manager.create_access_token.return_value = "test-token"
    
    token = create_access_token(user_data)
    
    assert isinstance(token, str)
    assert token == "test-token"
    
    # Verify the JWT manager was called correctly
    mock_jwt_manager.create_access_token.assert_called_once()
    call_args = mock_jwt_manager.create_access_token.call_args[0][0]
    assert call_args["sub"] == user_id
    assert call_args["role"] == "admin"
    assert call_args["name"] == "Test Admin"
    assert call_args["type"] == "access"
    assert "jti" in call_args