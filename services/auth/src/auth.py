# services/auth/auth.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db import get_db
from .crud import get_user_by_email, verify_password
from .models import User
from .config import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    description="OAuth2 password flow with Bearer tokens"
)

JWT_SECRET: str = settings.jwt_secret
ALGORITHM: str = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.access_token_expire_minutes


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    if "sub" not in data:
        raise ValueError("Field 'sub' (subject) is required in JWT payload")

    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        **data,
        "iat": now,
        "nbf": now,
        "exp": expire
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    logger.debug("Created JWT for sub=%s, expires at %s", data["sub"], expire.isoformat())
    return token


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        logger.info("Authentication failed: user %s not found", email)
        return None

    if not verify_password(password, user.password_hash):
        logger.info("Authentication failed: invalid password for %s", email)
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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id or not isinstance(user_id, str):
            logger.warning("JWT payload missing or invalid 'sub': %s", payload)
            raise credentials_exception
    except ExpiredSignatureError:
        logger.info("JWT token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers=auth_header,
        )
    except JWTError as err:
        logger.warning("JWT decode failed: %s", err)
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning("User not found for id=%s", user_id)
        raise credentials_exception

    return user