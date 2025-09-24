from collections.abc import Callable
from typing import Any

from aiogram import BaseMiddleware

from tele_store.db.db import db_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Any, data: dict[str, Any]):
        async with db_sessionmaker() as session:
            data["session"] = session
            return await handler(event, data)
