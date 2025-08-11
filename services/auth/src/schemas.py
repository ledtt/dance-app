# services/auth/schemas.py

import re
from typing import Literal, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, \
    SecretStr, field_validator
from shared.utils import sanitize_name, validate_password_strength_raise


class UserCreate(BaseModel):
    email: EmailStr = Field(
        ..., description="User email address, validated through EmailStr"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User name (1-100 characters)",
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)",
    )

    @field_validator('name')
    @classmethod
    def validate_and_sanitize_name(cls, v: str) -> str:
        return sanitize_name(v)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: SecretStr) -> SecretStr:
        validate_password_strength_raise(v.get_secret_value())
        return v


class UserOut(BaseModel):
    id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    is_active: bool = Field(..., description="User active status")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")
    role: str | None = Field(None, description="User role (admin or user)")

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User name (1-100 characters)",
    )

    @field_validator('name')
    @classmethod
    def validate_and_sanitize_name(cls, v: str) -> str:
        return sanitize_name(v)


class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(user|admin)$", description="User role (user or admin)")


class PasswordChange(BaseModel):
    current_password: SecretStr = Field(
        ..., description="Current password"
    )
    new_password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters)",
    )

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: SecretStr) -> SecretStr:
        validate_password_strength_raise(v.get_secret_value())
        return v


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    user_id: str | None = None
