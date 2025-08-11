# services/schedule/src/auth.py

from .config import settings
from shared.auth import (
    JWTManager, 
    create_get_current_user_dependency, 
    create_get_current_admin_user_dependency,
    create_verify_service_token_dependency,
    UserInToken
)

# 1. Создаем JWTManager для пользовательских токенов
jwt_manager = JWTManager(
    secret_key=settings.jwt_secret,
    algorithm=settings.jwt_algorithm
)

# 2. Создаем ОТДЕЛЬНЫЙ JWTManager для сервисных токенов
service_jwt_manager = JWTManager(
    secret_key=settings.service_jwt_secret or settings.jwt_secret,  # Fallback на обычный секрет если сервисный не задан
    algorithm=settings.jwt_algorithm
)

# 3. Используем фабрики для создания зависимостей
get_current_user = create_get_current_user_dependency(jwt_manager)
get_current_admin_user = create_get_current_admin_user_dependency(get_current_user)
verify_service_token = create_verify_service_token_dependency(service_jwt_manager)
