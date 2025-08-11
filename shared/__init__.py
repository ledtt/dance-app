# shared/__init__.py

from .auth import (
    JWTManager,
    create_get_current_user_dependency,
    create_get_current_admin_user_dependency,
    create_verify_service_token_dependency,
    UserInToken,
    hash_password,
    verify_password,
    oauth2_scheme
)

__all__ = [
    'JWTManager',
    'create_get_current_user_dependency',
    'create_get_current_admin_user_dependency',
    'create_verify_service_token_dependency',
    'UserInToken',
    'hash_password',
    'verify_password',
    'oauth2_scheme'
] 