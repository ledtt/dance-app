# shared/auth.py

import jwt
import structlog
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable, Coroutine
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from pydantic import BaseModel

logger = structlog.get_logger()

# Security scheme for JWT tokens
oauth2_scheme = HTTPBearer(auto_error=False)
oauth2_password_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- User Model ---
class UserInToken(BaseModel):
    id: str
    email: str
    name: str
    role: str


class JWTManager:
    """
    Shared JWT token management for all services.
    Handles token creation, validation, and user authentication.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token with the given data.
        
        Args:
            data: Dictionary containing token payload
            expires_delta: Optional expiration time delta
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        })
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.info("JWT token created", user_id=data.get("sub"), expires_at=expire.isoformat())
        return encoded_jwt
    
    def create_service_token(self, service_name: str, expires_minutes: int = 60) -> str:
        """
        Create a JWT token for inter-service communication.
        
        Args:
            service_name: Name of the service requesting the token
            expires_minutes: Token expiration time in minutes
            
        Returns:
            JWT token string
        """
        data = {
            "sub": f"service:{service_name}",
            "type": "service",
            "service": service_name
        }
        
        expires_delta = timedelta(minutes=expires_minutes)
        return self.create_access_token(data, expires_delta)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.InvalidTokenError, jwt.DecodeError) as e:
            logger.warning("Invalid JWT token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_service(self, token: str) -> Dict[str, Any]:
        """
        Get current service from JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Service information from token
            
        Raises:
            HTTPException: If token is invalid or not a service token
        """
        payload = self.verify_token(token)
        token_type = payload.get("type")
        
        if token_type != "service":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check for both "service" and "service_name" fields for compatibility
        service_name = payload.get("service_name") or payload.get("service")
        if not service_name:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "service": service_name,
            "token_payload": payload
        }


# --- ФАБРИКИ ЗАВИСИМОСТЕЙ ---

def create_get_current_user_dependency(jwt_manager: JWTManager) -> Callable[..., Coroutine[Any, Any, UserInToken]]:
    """
    Фабрика, которая СОЗДАЕТ и ВОЗВРАЩАЕТ функцию-зависимость для получения текущего пользователя.
    """
    async def get_current_user(token: str = Depends(oauth2_password_scheme)) -> UserInToken:
        try:
            payload = jwt_manager.verify_token(token)
            if payload.get("type") != "access":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
            
            user_data = {
                "id": payload.get("sub"),
                "email": payload.get("email", ""),
                "name": payload.get("name", ""),
                "role": payload.get("role", "user") # Default to 'user'
            }
            if not user_data["id"]:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

            return UserInToken(**user_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    return get_current_user


def create_get_current_admin_user_dependency(get_current_user_dep):
    """
    Фабрика, которая СОЗДАЕТ и ВОЗВРАЩАЕТ функцию-зависимость для проверки прав админа.
    """
    async def get_current_admin_user(current_user: UserInToken = Depends(get_current_user_dep)) -> UserInToken:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    
    return get_current_admin_user


def create_verify_service_token_dependency(jwt_manager: JWTManager):
    """
    Фабрика для создания зависимости проверки сервисных токенов.
    """
    async def verify_service_token_dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
    ) -> Dict[str, Any]:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return jwt_manager.get_current_service(credentials.credentials)
    
    return verify_service_token_dependency


# Utility functions for password hashing
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    import bcrypt
    # Handle both string and SecretStr objects
    if hasattr(hashed_password, 'get_secret_value'):
        hashed_password = hashed_password.get_secret_value()
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
