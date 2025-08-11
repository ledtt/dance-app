# services/schedule/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    
    # JWT configuration
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    
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
