# services/booking/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    
    # Service URLs
    schedule_service_url: str = Field(..., alias="SCHEDULE_SERVICE_URL")
    auth_service_url: str = Field(..., alias="AUTH_SERVICE_URL")
    
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
