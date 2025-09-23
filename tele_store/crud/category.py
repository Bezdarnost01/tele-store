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
        self: AsyncSession, *, name: str, description: str | None = None
    ) -> Category:
        """Создать новую категорию товаров."""
        category = Category(name=name, description=description)
        self.add(category)
        await self.commit()
        await self.refresh(category)
        return category


    @staticmethod
    async def get_category(self: AsyncSession, category_id: int) -> Category | None:
        """Получить категорию по идентификатору."""
        return await self.get(Category, category_id)


    @staticmethod
    async def list_categories(self: AsyncSession) -> list[Category]:
        """Вернуть все категории, отсортированные по имени."""
        result = await self.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())


    @staticmethod
    async def update_category(
        self: AsyncSession,
        category_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Category | None:
        """Обновить имя или описание категории."""
        category = await self.get(Category, category_id)
        if category is None:
            return None

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description

        if name is not None or description is not None:
            await self.commit()
            await self.refresh(category)

        return category


    @staticmethod
    async def delete_category(self: AsyncSession, category_id: int) -> bool:
        """Удалить категорию вместе со связанными товарами."""
        category = await self.get(Category, category_id)
        if category is None:
            return False

        await self.delete(category)
        await self.commit()
        return True
