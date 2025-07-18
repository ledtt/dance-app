# services/auth/crud.py

import logging
from typing import Optional

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import User
from .schemas import UserCreate

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    raw_password = user_create.password.get_secret_value()
    hashed_pw = pwd_context.hash(raw_password)

    new_user = User(
        email=user_create.email,
        name=user_create.name,
        password_hash=hashed_pw,
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        logger.info("User created: %s (id=%s)", new_user.email, new_user.id)
    except IntegrityError:
        await db.rollback()
        logger.warning("Registration failed, email exists: %s", user_create.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    return new_user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as e:
        logger.error("Password verify error: %s", e)
        return False
