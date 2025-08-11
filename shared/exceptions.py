# shared/exceptions.py

from typing import Optional, Dict, Any


class DanceAppException(Exception):
    """Base exception for the dance app"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DanceAppException):
    """Raised when input validation fails"""
    pass


class AuthenticationError(DanceAppException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(DanceAppException):
    """Raised when authorization fails"""
    pass


class ResourceNotFoundError(DanceAppException):
    """Raised when a requested resource is not found"""
    pass


class ResourceConflictError(DanceAppException):
    """Raised when there's a conflict with an existing resource"""
    pass


class CapacityExceededError(DanceAppException):
    """Raised when booking capacity is exceeded"""
    pass


class BookingError(DanceAppException):
    """Raised when booking operations fail"""
    pass


class ExternalServiceError(DanceAppException):
    """Raised when external service calls fail"""
    pass


class DatabaseError(DanceAppException):
    """Raised when database operations fail"""
    pass 