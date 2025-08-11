# shared/constants.py

from enum import Enum


class WeekDay(Enum):
    """Weekday enumeration"""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class BookingStatus(Enum):
    """Booking status enumeration"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class UserRole(Enum):
    """User role enumeration"""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class TokenType(Enum):
    """JWT token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"


# Application constants
MAX_CLASS_CAPACITY = 100
MIN_CLASS_CAPACITY = 1
MAX_USER_NAME_LENGTH = 100
MAX_CLASS_NAME_LENGTH = 100
MAX_TEACHER_NAME_LENGTH = 100
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Default values
DEFAULT_JWT_EXPIRY_MINUTES = 15
DEFAULT_RATE_LIMIT_LOGIN = "5/minute"
DEFAULT_RATE_LIMIT_REGISTER = "3/minute"

# Error messages
ERROR_MESSAGES = {
    "user_not_found": "User not found",
    "class_not_found": "Class not found",
    "booking_not_found": "Booking not found",
    "email_already_exists": "Email already registered",
    "invalid_credentials": "Invalid credentials",
    "capacity_exceeded": "Booking not possible - all spots are taken",
    "already_booked": "You are already booked for this class",
    "invalid_weekday": "Invalid weekday for this class",
    "past_date_booking": "Cannot book past dates",
    "invalid_token": "Invalid token",
    "token_expired": "Token has expired",
    "insufficient_permissions": "Insufficient permissions",
    "validation_error": "Validation error",
    "internal_error": "Internal server error",
    "external_service_error": "External service unavailable",
}

# Success messages
SUCCESS_MESSAGES = {
    "user_registered": "User registered successfully",
    "user_logged_in": "User logged in successfully",
    "booking_created": "Booking created successfully",
    "booking_cancelled": "Booking cancelled successfully",
    "class_created": "Class created successfully",
    "class_updated": "Class updated successfully",
    "class_deleted": "Class deleted successfully",
} 