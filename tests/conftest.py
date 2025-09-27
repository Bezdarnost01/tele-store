import os
from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMINS", "[1]")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ITEMS_PER_PAGE", "10")
os.environ.setdefault("ORDERS_PER_PAGE", "10")
os.environ.setdefault("CATEGORIES_PER_PAGE", "10")
os.environ.setdefault("PRODUCTS_PER_PAGE", "10")

from tele_store.db.db import Base


@pytest_asyncio.fixture
def event_loop():  # type: ignore[override]
    """Создаём отдельный событийный цикл для pytest-asyncio."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Асинхронная сессия SQLite в памяти для тестов."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:?cache=shared")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    testing_session = async_sessionmaker(engine, expire_on_commit=False)

    async with testing_session() as session:
        yield session

    await engine.dispose()
