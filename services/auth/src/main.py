# services/auth/main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import authenticate_user, create_access_token, get_current_user
from .db import get_db, init_db
from .crud import create_user, get_user_by_email
from .schemas import UserCreate, UserOut, Token

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации: регистрация, вход и выдача JWT-токенов",
    version="1.0.0",
    lifespan=lifespan,
)

@app.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    tags=["auth"],
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        logger.warning("Register failed — email exists: %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(db, user_data)
    logger.info("User registered: %s (id=%s)", user.email, user.id)
    return UserOut.model_validate(user)


@app.post(
    "/login",
    response_model=Token,
    summary="Получение JWT-токена",
    tags=["auth"],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.info("Login failed for %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id)})
    logger.info("JWT issued for %s", user.email)
    return Token(access_token=token, token_type="bearer")


@app.get(
    "/me",
    response_model=UserOut,
    summary="Информация о текущем пользователе",
    tags=["auth"],
)
async def read_current_user(
    current_user=Depends(get_current_user),
) -> UserOut:
    return UserOut.model_validate(current_user)
