# services/booking/src/auth.py

import structlog

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import settings
from shared.auth import (
    JWTManager, 
    create_get_current_user_dependency, 
    create_get_current_admin_user_dependency,
    UserInToken
)

logger = structlog.get_logger()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 1. Создаем ЕДИНСТВЕННЫЙ экземпляр JWTManager для этого сервиса
jwt_manager = JWTManager(
    secret_key=settings.jwt_secret,
    algorithm=settings.jwt_algorithm
)

# 2. Используем фабрики для создания зависимостей
get_current_user = create_get_current_user_dependency(jwt_manager)
get_current_admin_user = create_get_current_admin_user_dependency(get_current_user)

# Старые функции удалены - теперь используется унифицированный подход с UserInToken
