import sqlite3

from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from tele_store.config.config_reader import config

DATABASE_URL = config.DATABASE_URL

db_metadata = MetaData()


class Base(DeclarativeBase):
    metadata = db_metadata


db_engine = create_async_engine(DATABASE_URL)
db_sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)


@event.listens_for(db_engine.sync_engine, "connect")
def set_sqlite_pragma(
    dbapi_connection: sqlite3.Connection, _connection_record: object
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()


async def get_user_session() -> AsyncSession:
    async with db_sessionmaker() as session:
        yield session
