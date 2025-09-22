async def init_all_databases() -> None:
    """Создание таблиц в базе данных по описанию моделей."""
    import models.models  # noqa: F401
    from db.db import Base, db_engine

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
