# services/booking/service_auth.py
import structlog
from typing import Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from .config import settings

logger = structlog.get_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", description="OAuth2 password flow with Bearer tokens")

SERVICE_JWT_SECRET: str = settings.service_jwt_secret or settings.jwt_secret
ALGORITHM: str = settings.jwt_algorithm

def verify_service_token(token: str) -> Dict:
    """Verify service JWT token"""
    try:
        payload = jwt.decode(token, SERVICE_JWT_SECRET, algorithms=[ALGORITHM])
        service_name = payload.get("service_name")
        token_type = payload.get("type")
        
        if not service_name:
            logger.warning("Service token missing service_name")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token"
            )
        
        if token_type != "service":
            logger.warning("Service token has wrong type", token_type=token_type)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token"
            )
        
        logger.info("Service token verified", service_name=service_name)
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Service token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service token expired"
        )
    except JWTError as e:
        logger.warning("Service token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )

async def verify_service_token_dependency(authorization: str = Depends(oauth2_scheme)) -> Dict:
    """FastAPI dependency to verify service tokens"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    return verify_service_token(authorization)


# Service Token Manager for requesting tokens from auth-service
from typing import Optional
from datetime import datetime, timedelta
import httpx

class ServiceTokenManager:
    def __init__(self):
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._service_name = "booking-service"
    
    async def get_service_token(self) -> str:
        """Get a valid service token, either from cache or by requesting a new one"""
        now = datetime.utcnow()
        
        # Check if we have a valid cached token
        if (self._cached_token and self._token_expires_at and 
            now < self._token_expires_at - timedelta(minutes=1)):  # 1 minute buffer
            logger.info("Using cached service token")
            return self._cached_token
        
        # Request new token
        logger.info("Requesting new service token from auth-service")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {settings.internal_auth_token}"}
                url = f"{settings.auth_service_url}/auth/internal/service-token"
                logger.info(f"Making request to: {url}")
                logger.info(f"Headers: {headers}")
                logger.info(f"Params: service_name={self._service_name}")
                
                response = await client.post(
                    url,
                    headers=headers,
                    params={"service_name": self._service_name}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self._cached_token = token_data["access_token"]
                    # Set expiration time (subtract 1 minute for safety)
                    expires_in = token_data.get("expires_in", 300)  # 5 minutes default
                    self._token_expires_at = now + timedelta(seconds=expires_in - 60)
                    
                    logger.info("Service token obtained successfully", service_name=self._service_name)
                    return self._cached_token
                
                logger.error("Failed to obtain service token", 
                           status_code=response.status_code,
                           response_text=response.text)
                raise HTTPException(
                    status_code=503,
                    detail="Failed to obtain service token"
                )
                    
        except httpx.TimeoutException:
            logger.error("Timeout while requesting service token")
            raise HTTPException(
                status_code=503,
                detail="Auth service timeout"
            )
        except httpx.RequestError as e:
            logger.error("Request error while obtaining service token", error=str(e))
            raise HTTPException(
                status_code=503,
                detail="Auth service unavailable"
            )
        except Exception as e:
            logger.error("Unexpected error while obtaining service token", error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

# Global instance
service_token_manager = ServiceTokenManager()
