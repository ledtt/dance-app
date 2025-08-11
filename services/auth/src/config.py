# services/auth/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET", min_length=32)
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")  # Reduced from 30
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Security settings
    cors_origins: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")
    trusted_hosts: list[str] = Field(default=["localhost", "127.0.0.1"], alias="TRUSTED_HOSTS")
    
    # Rate limiting
    rate_limit_login: str = Field(default="5/minute", alias="RATE_LIMIT_LOGIN")
    rate_limit_register: str = Field(default="3/minute", alias="RATE_LIMIT_REGISTER")
    
    # Internal service authentication
    internal_auth_token: str = Field(default="internal-secret-token", alias="INTERNAL_AUTH_TOKEN")
    
    # Service JWT configuration
    service_token_expire_minutes: int = Field(default=5, alias="SERVICE_TOKEN_EXPIRE_MINUTES")
    service_jwt_secret: str = Field(default="", alias="SERVICE_JWT_SECRET")
    
    @field_validator('service_jwt_secret')
    @classmethod
    def validate_service_jwt_secret(cls, v: str) -> str:
        if not v:
            # If not provided, use the main JWT secret
            return ""
        if len(v) < 32:
            raise ValueError("SERVICE_JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @field_validator('access_token_expire_minutes')
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        if v < 1 or v > 60:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 60")
        return v

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="",
        populate_by_name=True,
        extra="ignore",
    )

settings = Settings()  # type: ignore
