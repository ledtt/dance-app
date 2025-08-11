# services/booking/schemas.py

import datetime
import re
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import date


class ExternalClassOut(BaseModel):
    id: UUID = Field(..., description="Class ID")
    name: str = Field(..., description="Class name")
    teacher: str = Field(..., description="Teacher name")
    weekday: int = Field(..., description="Day of week (1-7)")
    start_time: str = Field(..., description="Class start time")
    capacity: int = Field(..., description="Class capacity")
    active: bool = Field(..., description="Class active status")
    created_at: datetime.datetime = Field(..., description="Class creation date")


    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    class_id: UUID = Field(..., description="Class ID for booking")
    date: datetime.date = Field(
        ..., 
        description="Class date",
        ge=datetime.date.today()  # Cannot book past dates
    )
    user_id: Optional[UUID] = Field(None, description="User ID (required for admin bookings)")

    @field_validator('date')
    @classmethod
    def validate_future_date(cls, v):
        if v < datetime.date.today():
            raise ValueError("Cannot book past dates")
        return v
    
    @field_validator('class_id')
    @classmethod
    def validate_class_id(cls, v):
        if not v:
            raise ValueError("Class ID is required")
        return v


class ExternalUserOut(BaseModel):
    id: UUID = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    created_at: datetime.datetime = Field(..., description="User creation date")

    model_config = ConfigDict(from_attributes=True)


class BookingOut(BaseModel):
    id: UUID = Field(..., description="Booking ID")
    class_id: UUID = Field(..., description="Class ID")
    user_id: UUID = Field(..., description="User ID")
    date: datetime.date = Field(..., description="Class date")
    start_time: datetime.datetime = Field(..., description="Class start time")
    created_at: datetime.datetime = Field(..., description="Booking creation date")
    class_info: Optional[ExternalClassOut] = Field(None, description="Class information")
    user: Optional[ExternalUserOut] = Field(None, description="User information")

    model_config = ConfigDict(from_attributes=True)


class BookingFilterParams(BaseModel):
    """Pydantic model for booking filter parameters"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    user_id: Optional[UUID] = None
    teacher: Optional[str] = None
    class_name: Optional[str] = None
    class_id: Optional[UUID] = None
    limit: int = 100
    offset: int = 0
