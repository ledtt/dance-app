# services/auth/crud.py

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from .models import User
from .schemas import UserCreate, UserUpdate
from shared.auth import hash_password, verify_password

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    try:
        # Handle both string and UUID objects
        if isinstance(user_id, str):
            uuid_obj = UUID(user_id)
        else:
            uuid_obj = user_id
    except (ValueError, AttributeError):
        return None
    
    result = await db.execute(select(User).where(User.id == uuid_obj))
    return result.scalar_one_or_none()


async def get_all_users(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 50,
    email: Optional[str] = None,
    name: Optional[str] = None
) -> List[User]:
    """Get all users with optional filtering and pagination"""
    query = select(User)
    
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
    
    if name:
        query = query.where(User.name.ilike(f"%{name}%"))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_users_count(
    db: AsyncSession,
    email: Optional[str] = None,
    name: Optional[str] = None
) -> int:
    """Get the total count of users with optional filtering"""
    query = select(func.count()).select_from(User)
    
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
    
    if name:
        query = query.where(User.name.ilike(f"%{name}%"))
    
    result = await db.execute(query)
    return result.scalar_one()


async def get_admin_count(db: AsyncSession) -> int:
    """Get the total count of admin users"""
    result = await db.execute(
        select(func.count()).select_from(User).where(User.role == "admin")
    )
    return result.scalar_one()


async def create_user(db: AsyncSession, user_create: UserCreate, is_admin: bool = False) -> User:
    raw_password = user_create.password.get_secret_value()
    hashed_pw = hash_password(raw_password)

    new_user = User(
        email=user_create.email,
        name=user_create.name,
        password_hash=hashed_pw,
        role="admin" if is_admin else "user",
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        role_text = "admin" if is_admin else "user"
        logger.info("User created: %s (id=%s, role=%s)", new_user.email, new_user.id, role_text)
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("Registration failed, email exists: %s", user_create.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        ) from exc
    return new_user


async def update_user_role(db: AsyncSession, user_id: UUID, role: str, current_user_id: Optional[UUID] = None) -> Optional[User]:
    """Update user's role with validation"""
    user = await get_user_by_id(db, str(user_id))
    if not user:
        return None
    
    # If we're changing from admin to user, check if this would leave no admins
    if user.role == "admin" and role == "user":
        admin_count = await get_admin_count(db)
        
        # If this is the only admin, prevent the change
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin privileges from the last administrator"
            )
        
        # If current user is trying to remove their own admin role, prevent it
        if current_user_id and str(user_id) == str(current_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove your own admin privileges"
            )
    
    user.role = role
    await db.commit()
    await db.refresh(user)
    logger.info("User role updated: %s (id=%s, role=%s)", user.email, user.id, role)
    return user


async def update_user(db: AsyncSession, user_id: str, user_update: UserUpdate) -> User:
    """Update user's name"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user name
    user.name = user_update.name
    
    try:
        await db.commit()
        await db.refresh(user)
        logger.info("User name updated: %s (id=%s)", user.email, user.id)
    except IntegrityError as exc:
        await db.rollback()
        logger.error("User update failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        ) from exc
    
    return user


async def change_user_password(db: AsyncSession, user_id: str, new_password: str) -> None:
    """Change user's password"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash new password using shared function
    hashed_pw = hash_password(new_password)
    user.password_hash = hashed_pw
    
    try:
        await db.commit()
        logger.info("Password changed for user: %s (id=%s)", user.email, user.id)
    except IntegrityError as exc:
        await db.rollback()
        logger.error("Password change failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        ) from exc


# Password verification is now handled by the shared auth library
# The verify_password function is imported from shared.auth
