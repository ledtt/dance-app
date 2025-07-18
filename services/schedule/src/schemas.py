# services/schedule/schemas.py

from datetime import time, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    name: str
    teacher: str
    weekday: int = Field(ge=1, le=7, description="1 = Пн, ..., 7 = Вс")
    time: time
    capacity: int = Field(gt=0)


class ClassOut(ClassCreate):
    id: UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
