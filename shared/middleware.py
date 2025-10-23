"""
Custom middleware for dance-app services
"""

from fastapi import Request, HTTPException, status
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware


class CustomTrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Custom TrustedHostMiddleware that excludes health endpoint from host validation.
    This allows ALB health checks to work while maintaining security for other endpoints.
    """
    
    def __init__(self, app, allowed_hosts: List[str]):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts
    
    async def dispatch(self, request: Request, call_next):
        # Skip host validation for health endpoint
        if request.url.path == "/health":
            return await call_next(request)
        
        # For all other endpoints, check if host is allowed
        host = request.headers.get("host", "")
        if not host:
            # If no host header, allow the request (for health checks)
            return await call_next(request)
        
        # Extract hostname without port for comparison
        hostname = host.split(":")[0] if ":" in host else host
        
        # Check if hostname is in allowed hosts
        if hostname in self.allowed_hosts:
            return await call_next(request)
        
        # Host not allowed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid host header: {host} (extracted hostname: {hostname}, allowed: {self.allowed_hosts})"
        )
