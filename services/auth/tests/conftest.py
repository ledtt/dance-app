# tests/conftest.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import engine
from src.models import Base
from sqlalchemy.ext.asyncio import async_sessionmaker


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
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session