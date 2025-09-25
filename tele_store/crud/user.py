from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from tele_store.models.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserManager:
    """Класс для управления пользователями в базе данных."""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        *,
        tg_id: int,
    ) -> User:
        """Создать пользователя."""
        user = User(tg_id=tg_id)
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise
        else:
            await session.refresh(user)
            return user

    async def get_user(session: AsyncSession, tg_id: int) -> User | None:
        """Получить пользователя по идентификатору."""
        res = await session.execute(select(User).where(User.tg_id == tg_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_users(
        session: AsyncSession,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        """Вернуть список пользователей, упорядоченный по идентификатору."""
        stmt: Select[tuple[User]] = select(User).order_by(User.id).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя вместе с его корзиной и заказами."""
        user = await session.get(User, user_id)
        if user is None:
            return False

        await session.delete(user)
        await session.commit()
        return True
