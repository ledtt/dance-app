# services/auth/db.py

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from .config import settings
from .models import Base 

logger = logging.getLogger(__name__)

DATABASE_URL: str = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    async with engine.begin() as conn:
        # Create tables
        try:
            await conn.run_sync(Base.metadata.create_all)
            
            # Add is_active column if it doesn't exist
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            await conn.commit()
            logger.info("Database initialized successfully")
        except Exception as exc:
            logger.error("Failed to create database tables: %s", str(exc))
            raise
