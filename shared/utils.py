# shared/utils.py

import re
from typing import Optional
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()


def sanitize_name(name: str) -> str:
    """Sanitize name by removing dangerous content and characters"""
    if not name:
        return name
    
    # Remove HTML tags and potentially dangerous content
    # First remove HTML tags
    sanitized = re.sub(r'<[^>]+>', '', name.strip())
    # Remove potentially dangerous JavaScript patterns
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'alert\s*\([^)]*\)', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'confirm\s*\([^)]*\)', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'prompt\s*\([^)]*\)', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'eval\s*\([^)]*\)', '', sanitized, flags=re.IGNORECASE)
    # Remove remaining dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    # Clean up multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def validate_password_strength_raise(password: str) -> str:
    """Validate password strength and raise ValueError if invalid"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must contain at least 8 characters")
    
    if not any(c.isalpha() for c in password):
        errors.append("Password must contain at least one letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    if len(errors) > 0:
        raise ValueError(", ".join(errors))
    
    return password


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input by removing dangerous characters"""
    if not value:
        return value
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', value.strip())
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength and return (is_valid, errors)"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must contain at least 8 characters")
    
    if not any(c.isalpha() for c in password):
        errors.append("Password must contain at least one letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def get_current_timestamp() -> datetime:
    """Get current timestamp in UTC"""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
    """Parse datetime from string"""
    return datetime.strptime(date_str, format_str)


def log_security_event(event_type: str, user_id: Optional[str] = None, details: Optional[dict] = None):
    """Log security-related events"""
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        details=details,
        timestamp=get_current_timestamp().isoformat()
    )


def log_performance_metric(metric_name: str, value: float, unit: str = "ms"):
    """Log performance metrics"""
    logger.info(
        "Performance metric",
        metric_name=metric_name,
        value=value,
        unit=unit,
        timestamp=get_current_timestamp().isoformat()
    ) 