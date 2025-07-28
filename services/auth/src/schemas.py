# services/auth/schemas.py

from typing import Literal, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, \
    SecretStr, ValidationInfo, model_validator



class UserCreate(BaseModel):
    email: EmailStr = Field(
        ..., description="Почта пользователя, проверяется через EmailStr"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя пользователя (1–100 символов)",
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        description="Пароль (не менее 8 символов)",
    )

    @model_validator(mode="before")
    @classmethod
    def check_password_complexity(
        cls, data: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        pwd = data.get("password")
        if pwd is None:
            return data

        if isinstance(pwd, SecretStr):
            raw = pwd.get_secret_value()
        else:
            raw = str(pwd)

        if not any(c.isalpha() for c in raw) or not any(c.isdigit() for c in raw):
            raise ValueError("Пароль должен содержать и буквы, и цифры")

        return data


class UserOut(BaseModel):
    id: UUID = Field(..., description="UUID пользователя")
    email: EmailStr = Field(..., description="Почта пользователя")
    name: str = Field(..., description="Имя пользователя")
    created_at: datetime = Field(..., description="Время создания записи")
    updated_at: datetime = Field(..., description="Время последнего обновления")
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str = Field(..., description="JWT для доступа")
    token_type: Literal["bearer"] = Field(
        "bearer", description="Тип токена (должно быть 'bearer')"
    )
