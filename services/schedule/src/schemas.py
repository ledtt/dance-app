# services/schedule/schemas.py

import re
from datetime import time, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shared.utils import sanitize_name


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Class name")
    teacher: str = Field(..., min_length=1, max_length=100, description="Teacher name")
    weekday: int = Field(..., ge=1, le=7, description="1 = Monday, ..., 7 = Sunday")
    start_time: time = Field(..., description="Class start time")
    capacity: int = Field(..., gt=0, le=100, description="Maximum number of participants")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment about the class")

    @field_validator('weekday')
    @classmethod
    def validate_weekday(cls, v):
        if not isinstance(v, int) or v < 1 or v > 7:
            raise ValueError("Weekday must be an integer between 1 and 7")
        return v

    @field_validator('name', 'teacher')
    @classmethod
    def sanitize_string(cls, v):
        sanitized = sanitize_name(v)
        if not sanitized:
            raise ValueError("Field cannot be empty after sanitization")
        return sanitized

    @field_validator('capacity')
    @classmethod
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("Capacity must be greater than 0")
        if v > 100:
            raise ValueError("Capacity cannot exceed 100")
        return v

    @field_validator('comment')
    @classmethod
    def sanitize_comment(cls, v):
        if v is None:
            return v
        return sanitize_name(v)

    @field_validator('start_time', mode='before')
    @classmethod
    def parse_start_time(cls, v):
        """Convert string time to datetime.time object"""
        if isinstance(v, str):
            try:
                hour, minute = map(int, v.split(':'))
                return time(hour, minute)
            except (ValueError, TypeError):
                raise ValueError("Invalid time format. Expected HH:MM format.")
        return v


class ClassOut(ClassCreate):
    id: UUID = Field(..., description="Class ID")
    active: bool = Field(..., description="Whether the class is active")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: datetime = Field(..., description="Last update date")

    model_config = ConfigDict(from_attributes=True)
