from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from tele_store.models.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.schemas.user import CreateUser, UserUpdate


class UserManager:
    """Класс для управления пользователями в базе данных."""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        *,
        payload: CreateUser,
    ) -> User:
        """Создать пользователя."""
        user = User(
            user_id=payload.user_id,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
        )
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise
        else:
            await session.refresh(user)
            return user

    async def get_user(self: AsyncSession, user_id: int) -> User | None:
        """Получить пользователя по идентификатору."""
        return await self.get(User, user_id)

    @staticmethod
    async def list_users(
        self: AsyncSession,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        """Вернуть список пользователей, упорядоченный по идентификатору."""
        stmt: Select[tuple[User]] = select(User).order_by(User.id).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_user(
        self: AsyncSession, user_id: int, payload: UserUpdate
    ) -> User | None:
        """Обновить данные пользователя."""
        user = await self.get(User, user_id)
        if user is None:
            return None

        updates = payload.model_dump(exclude_unset=True, exclude_none=True)
        for attr, value in updates.items():
            setattr(user, attr, value)

        if updates:
            await self.commit()
            await self.refresh(user)
        return user

    @staticmethod
    async def delete_user(self: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя вместе с его корзиной и заказами."""
        user = await self.get(User, user_id)
        if user is None:
            return False

        await self.delete(user)
        await self.commit()
        return True
