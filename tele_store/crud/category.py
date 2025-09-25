from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from tele_store.models.models import Category

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CategoryManager:
    """Класс управления категориями товаров в базе данных"""

    @staticmethod
    async def create_category(
        session: AsyncSession, *, name: str, description: str | None = None
    ) -> Category:
        """Создать новую категорию товаров."""
        category = Category(name=name, description=description)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def get_category(session: AsyncSession, category_id: int) -> Category | None:
        """Получить категорию по идентификатору."""
        return await session.get(Category, category_id)

    @staticmethod
    async def list_categories(session: AsyncSession) -> list[Category]:
        """Вернуть все категории, отсортированные по имени."""
        result = await session.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    @staticmethod
    async def update_category(
        session: AsyncSession,
        category_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Category | None:
        """Обновить имя или описание категории."""
        category = await session.get(Category, category_id)
        if category is None:
            return None

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description

        if name is not None or description is not None:
            await session.commit()
            await session.refresh(category)

        return category

    @staticmethod
    async def delete_category(session: AsyncSession, category_id: int) -> bool:
        """Удалить категорию вместе со связанными товарами."""
        category = await session.get(Category, category_id)
        if category is None:
            return False

        await session.delete(category)
        await session.commit()
        return True
