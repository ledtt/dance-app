# services/schedule/config.py

import os
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET", min_length=32)
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    
    # Security settings
    cors_origins: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")
    allowed_hosts: list[str] = Field(default=["localhost", "127.0.0.1"], alias="ALLOWED_HOSTS")
    
    # Internal service authentication
    internal_auth_token: str = Field(default="internal-secret-token", alias="INTERNAL_AUTH_TOKEN")
    
    # Service JWT configuration
    service_token_expire_minutes: int = Field(default=5, alias="SERVICE_TOKEN_EXPIRE_MINUTES")
    service_jwt_secret: str = Field(default="", alias="SERVICE_JWT_SECRET")
    
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="",
        populate_by_name=True,
        extra="ignore",
    )

settings = Settings()  # type: ignore
