"""Общие фикстуры для тестов CRUD и миграций."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

# Значения по умолчанию позволяют импортировать модули настроек приложения.
os.environ.setdefault("BOT_TOKEN", "TEST_TOKEN")
os.environ.setdefault("ADMINS", "[1]")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _make_alembic_config(database_url: str) -> Config:
    """Создать конфигурацию Alembic для указанного URL."""
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic_migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    cfg.attributes["configure_logger"] = False
    return cfg


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Предоставить отдельный цикл событий для pytest-asyncio."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture
def migrated_database(tmp_path: Path) -> Iterator[str]:
    """Создать чистую тестовую базу данных и применить миграции Alembic."""
    db_file = tmp_path / "test.sqlite3"
    database_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    os.environ["DATABASE_URL"] = database_url

    cfg = _make_alembic_config(database_url)
    command.upgrade(cfg, "head")

    try:
        yield database_url
    finally:
        command.downgrade(cfg, "base")
        if db_file.exists():
            db_file.unlink()


@pytest_asyncio.fixture
async def session(migrated_database: str) -> AsyncIterator[AsyncSession]:
    """Подключиться к тестовой базе и вернуть асинхронную сессию."""
    engine: AsyncEngine = create_async_engine(migrated_database, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            yield db_session
    finally:
        await engine.dispose()
