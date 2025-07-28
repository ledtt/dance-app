# tests/conftest.py

import pytest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.auth.src.db import engine
from services.auth.src.models import Base

@pytest.fixture(scope="function", autouse=True)
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture()
async def async_session():
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session