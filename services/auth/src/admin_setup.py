# services/auth/admin_setup.py

import structlog
from .config import settings
from .crud import get_user_by_email, create_user
from .schemas import UserCreate
from .db import get_db

logger = structlog.get_logger()

async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        # Get database session
        async for db in get_db():
            # Check if admin already exists
            existing_admin = await get_user_by_email(db, settings.admin_email)
            if existing_admin:
                logger.info("Admin user already exists", email=settings.admin_email)
                return
            
            # Create admin user
            admin_data = UserCreate(
                email=settings.admin_email,
                name="Default Admin",  # Можно вынести в переменные окружения
                password=settings.admin_password
            )
            
            admin_user = await create_user(db, admin_data, is_admin=True)
            logger.info("Default admin user created successfully", 
                       email=settings.admin_email, 
                       name=admin_user.name,
                       user_id=str(admin_user.id),
                       role=admin_user.role)
            break
            
    except Exception as e:
        logger.error("Failed to create default admin user", 
                    error=str(e), 
                    email=settings.admin_email)
        # Don't fail the startup if admin creation fails
