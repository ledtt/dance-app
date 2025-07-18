# services/booking/schemas.py

import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class BookingCreate(BaseModel):
    class_id: UUID
    date: datetime.date = Field(..., description="Дата проведения занятия")


class BookingOut(BaseModel):
    id: UUID
    class_id: UUID
    user_id: UUID
    date: datetime.date
    start_time: datetime.datetime
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
