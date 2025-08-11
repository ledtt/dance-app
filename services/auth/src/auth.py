# services/auth/auth.py

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from .db import get_db
from .crud import get_user_by_email
from .models import User
from .config import settings
from shared.auth import JWTManager, verify_password

logger = structlog.get_logger()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    description="OAuth2 password flow with Bearer tokens"
)

# Initialize shared JWT manager
jwt_manager = JWTManager(
    secret_key=settings.jwt_secret,
    algorithm=settings.jwt_algorithm
)

# Service JWT configuration
SERVICE_JWT_SECRET: str = settings.service_jwt_secret or settings.jwt_secret
SERVICE_TOKEN_EXPIRE_MINUTES: int = settings.service_token_expire_minutes


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token using shared JWT manager"""
    if "sub" not in data:
        raise ValueError("Field 'sub' (subject) is required in JWT payload")

    # Add token metadata
    payload = {
        **data,
        "jti": str(uuid.uuid4()),  # Add JWT ID for token tracking
        "type": "access",  # Token type for better security
        "role": data.get("role", "user")  # Add user role to token
    }

    # Use shared JWT manager
    expires_delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return jwt_manager.create_access_token(payload, expires_delta)


def create_service_token(service_name: str) -> str:
    """Create JWT token for inter-service communication using shared JWT manager"""
    if not service_name:
        raise ValueError("Service name is required")
    
    # Use shared JWT manager with service configuration
    service_jwt_manager = JWTManager(
        secret_key=SERVICE_JWT_SECRET,
        algorithm=settings.jwt_algorithm
    )
    
    data = {
        "sub": f"service:{service_name}",
        "service_name": service_name,
        "jti": str(uuid.uuid4()),
        "type": "service",  # Different type for service tokens
        "role": "service"
    }
    
    expires_delta = timedelta(minutes=SERVICE_TOKEN_EXPIRE_MINUTES)
    return service_jwt_manager.create_access_token(data, expires_delta)


def verify_service_token(token: str) -> dict:
    """Verify service JWT token and return payload using shared JWT manager"""
    # Use shared JWT manager with service configuration
    service_jwt_manager = JWTManager(
        secret_key=SERVICE_JWT_SECRET,
        algorithm=settings.jwt_algorithm
    )
    
    try:
        payload = service_jwt_manager.verify_token(token)
        
        # Check token type
        if payload.get("type") != "service":
            raise ValueError("Invalid token type - expected service token")
        
        # Check if service_name is present
        service_name = payload.get("service_name")
        if not service_name:
            raise ValueError("Service token missing service_name")
        
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Service JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        logger.info("Authentication failed - user not found")
        return None

    if not verify_password(password, user.password_hash):
        logger.info("Authentication failed - invalid password")
        return None

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    auth_header = {"WWW-Authenticate": "Bearer"}
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers=auth_header,
    )

    try:
        # Check internal token
        internal_token = settings.internal_auth_token
        if token == internal_token:
            # For internal requests return special user
            return User(
                id="internal",
                email="internal@service",
                name="Internal Service",
                password_hash="",
                is_active=True,
                role="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

        # Use shared JWT manager to verify token
        payload = jwt_manager.verify_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or not isinstance(user_id, str):
            logger.warning("JWT payload missing or invalid 'sub'")
            raise credentials_exception
            
        if token_type != "access":
            logger.warning("Invalid token type")
            raise credentials_exception
            
    except HTTPException:
        raise
    except Exception as err:
        logger.warning("JWT verification failed", error=str(err))
        raise credentials_exception from err

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning("User not found for token", user_id=user_id)
        raise credentials_exception

    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure current user is an admin"""
    if current_user.role != "admin":
        logger.warning("Admin access denied", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def verify_service_token_dependency(
    authorization: str = Depends(oauth2_scheme)
) -> dict:
    """Dependency to verify service JWT tokens"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    return verify_service_token(authorization)
    