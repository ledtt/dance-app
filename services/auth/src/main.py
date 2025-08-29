# services/auth/main.py

import logging
import structlog
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .auth import authenticate_user, create_access_token, create_service_token, get_current_user, get_current_admin_user, verify_service_token_dependency, oauth2_scheme
from shared.auth import verify_password
from shared.middleware import CustomTrustedHostMiddleware
from .db import get_db, init_db
from .crud import create_user, get_user_by_email, get_user_by_id, update_user, get_all_users, change_user_password, update_user_role, get_users_count
from .schemas import UserCreate, UserOut, Token, UserUpdate, PasswordChange, UserRoleUpdate
from shared.schemas import PaginatedResponse
from .config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_paginated_response(items: List, total: int, page: int, size: int) -> PaginatedResponse:
    """Create a paginated response with calculated pages"""
    pages = (total + size - 1) // size if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

# Rate limiter - only enable in non-testing mode
limiter = Limiter(key_func=get_remote_address)

def conditional_rate_limit(limit_string: str):
    """Apply rate limiting only if not in testing mode"""
    if os.getenv("TESTING_MODE") == "true":
        return lambda func: func  # No-op decorator
    return limiter.limit(limit_string)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Auth Service",
    description="Authentication service: registration, login and JWT token issuance",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state only if not in testing mode
if os.getenv("TESTING_MODE") != "true":
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add custom trusted host middleware (excludes health endpoint from validation)
app.add_middleware(
    CustomTrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

@app.get("/health")
async def health_check():
    """Health check endpoint for AWS monitoring"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@app.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    tags=["auth"],
)
@conditional_rate_limit(settings.rate_limit_register)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        logger.warning("Registration failed - email already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(db, user_data)
    logger.info("User registered successfully", user_id=str(user.id))
    return UserOut.model_validate(user)


@app.post(
    "/login",
    response_model=Token,
    summary="Get JWT token",
    tags=["auth"],
)
@conditional_rate_limit(settings.rate_limit_login)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning("Login failed - invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user role from database
    user_role = user.role
    
    token = create_access_token({
        "sub": str(user.id),
        "role": user_role
    })
    expires_in = settings.access_token_expire_minutes * 60  # Convert to seconds
    logger.info("JWT issued successfully", user_id=str(user.id), role=user_role)
    return Token(access_token=token, token_type="bearer", expires_in=expires_in)


@app.post(
    "/auth/internal/service-token",
    response_model=Token,
    summary="Get service JWT token",
    tags=["internal"],
)
async def get_service_token(
    service_name: str,
    internal_token: str = Depends(oauth2_scheme)
) -> Token:
    """Generate JWT token for inter-service communication"""
    # Verify internal token
    if internal_token != settings.internal_auth_token:
        logger.warning("Invalid internal token used for service token request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token"
        )
    
    if not service_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service name is required"
        )
    
    access_token = create_service_token(service_name)
    logger.info("Service token created", service_name=service_name)
    
    return Token(
        access_token=access_token, 
        token_type="bearer", 
        expires_in=settings.service_token_expire_minutes * 60
    )


@app.get(
    "/me",
    response_model=UserOut,
    summary="Current user information",
    tags=["auth"],
)
async def read_current_user(
    current_user=Depends(get_current_user),
) -> UserOut:
    # Get user role from database
    user_role = current_user.role
    
    # Create a dict with user data and role
    user_data = UserOut.model_validate(current_user).model_dump()
    user_data["role"] = user_role
    
    return UserOut(**user_data)

@app.put(
    "/me",
    response_model=UserOut,
    summary="Update current user profile",
    tags=["auth"],
)
async def update_current_user(
    user_update: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Update current user's name"""
    updated_user = await update_user(db, current_user.id, user_update)
    logger.info("User profile updated", user_id=str(current_user.id))
    
    # Get user role from database
    user_role = updated_user.role
    
    # Create a dict with user data and role
    user_data = UserOut.model_validate(updated_user).model_dump()
    user_data["role"] = user_role
    
    return UserOut(**user_data)

@app.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user password",
    tags=["auth"],
)
async def change_password(
    password_data: PasswordChange,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning("Password change failed - invalid current password", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password",
        )
    
    # Change password
    await change_user_password(db, current_user.id, password_data.new_password)
    logger.info("Password changed successfully", user_id=str(current_user.id))

@app.get(
    "/admin/users",
    response_model=PaginatedResponse[UserOut],
    summary="Get all users (admin only)",
    tags=["admin"],
)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    email: Optional[str] = Query(None, description="Filter by email"),
    name: Optional[str] = Query(None, description="Filter by name"),
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserOut]:
    """Get all users with pagination and filtering (admin only)"""
    # Calculate offset from page and size
    skip = (page - 1) * size
    
    # Get both the items and the total count in parallel
    users_task = get_all_users(db, skip=skip, limit=size, email=email, name=name)
    count_task = get_users_count(db, email=email, name=name)
    
    users, total_count = await asyncio.gather(users_task, count_task)
    
    # Add role information to each user
    result = []
    for user in users:
        user_data = UserOut.model_validate(user).model_dump()
        user_data["role"] = user.role
        result.append(UserOut(**user_data))
    
    logger.info("Users retrieved by admin", admin_id=str(current_user.id), count=len(result), total=total_count)
    return create_paginated_response(result, total_count, page, size)

@app.put(
    "/admin/users/{user_id}/role",
    response_model=UserOut,
    summary="Update user role (admin only)",
    tags=["admin"],
)
async def set_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Update user role (admin only)"""
    updated_user = await update_user_role(db, user_id, role_update.role, current_user_id=current_user.id)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    logger.info("User role updated by admin", admin_id=str(current_user.id), user_id=str(user_id), new_role=role_update.role)
    return UserOut.model_validate(updated_user)

@app.get(
    "/admin/users/{user_id}",
    response_model=UserOut,
    summary="Get user by ID (admin only)",
    tags=["admin"],
)
async def get_user_by_id_endpoint(
    user_id: str,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Get a specific user by ID (admin only)"""
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get user role from database
        user_role = user.role
        
        # Create a dict with user data and role
        user_data = UserOut.model_validate(user).model_dump()
        user_data["role"] = user_role
        
        logger.info("User retrieved by admin", admin_id=str(current_user.id), user_id=user_id)
        return UserOut(**user_data)
    except Exception as e:
        logger.error("Error getting user by ID", error=str(e), user_id=user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get(
    "/internal/users/{user_id}",
    response_model=UserOut,
    summary="Get user by ID (internal service use)",
    tags=["internal"],
)
async def get_user_by_id_internal(
    user_id: str,
    service_token: dict = Depends(verify_service_token_dependency),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Get a specific user by ID (internal service use, no auth required)"""
    try:
        logger.info("Internal service requesting user", user_id=user_id)
        user = await get_user_by_id(db, user_id)
        if not user:
            logger.warning("User not found", user_id=user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get user role from database
        user_role = user.role
        
        # Create a dict with user data and role
        user_data = UserOut.model_validate(user).model_dump()
        user_data["role"] = user_role
        
        logger.info("User retrieved by internal service", user_id=user_id, user_email=user.email)
        return UserOut(**user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user by ID (internal)", error=str(e), user_id=user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
