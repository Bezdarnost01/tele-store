from tele_store.db.db import Base, db_engine
from tele_store.models import models as _models  # noqa: F401


async def init_all_databases() -> None:
    """Создание таблиц в базе данных по описанию моделей."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
