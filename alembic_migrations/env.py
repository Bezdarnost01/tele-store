"""Alembic environment configured for asynchronous SQLAlchemy engine."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

# Подготавливаем переменные окружения до импорта настроек приложения.
config = context.config


def _ensure_env_defaults() -> None:
    """Назначить значения переменных окружения для импорта."""
    default_database_url = config.get_main_option(
        "sqlalchemy.url", "sqlite+aiosqlite:///./tele_store.db"
    )
    os.environ.setdefault("BOT_TOKEN", "migration-placeholder-token")
    os.environ.setdefault("ADMINS", "1")
    os.environ.setdefault("DATABASE_URL", default_database_url)


_ensure_env_defaults()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Импортируем базу и модели только после установки переменных окружения.
from tele_store.db.db import Base  # noqa: E402
from tele_store.models import models as _models  # noqa: F401,E402

target_metadata = Base.metadata


def get_url() -> str:
    """Получить URL базы данных из переменных окружения или конфигурации."""
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Запустить миграции в офлайн-режиме."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполнить миграции для предоставленного соединения."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Асинхронно запустить миграции в режиме online."""
    connectable: AsyncEngine = create_async_engine(get_url(), poolclass=pool.NullPool)

    try:
        async with connectable.begin() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Точка входа Alembic для режима online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
