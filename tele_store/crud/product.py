from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from tele_store.models.models import Product

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.schemas.product import CreateProduct, ProductUpdate


class ProductManager:
    """Класс для управления товарами в базе данных"""

    @staticmethod
    async def create_product(
        session: AsyncSession, *, payload: CreateProduct
    ) -> Product:
        """Создать товар и привязать его к категории."""
        product = Product(
            category_id=payload.category_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            photo_file_id=payload.photo_file_id,
            is_active=payload.is_active,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    @staticmethod
    async def get_product(session: AsyncSession, product_id: int) -> Product | None:
        """Получить товар по идентификатору вместе с категорией."""
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_products(
        session: AsyncSession,
        *,
        category_id: int | None = None,
        only_active: bool = True,
    ) -> list[Product]:
        """Вернуть список товаров, опционально отфильтрованных по категории."""
        stmt: Select[tuple[Product]] = select(Product).order_by(Product.name)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if only_active:
            stmt = stmt.where(Product.is_active.is_(True))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_product(
        session: AsyncSession, product_id: int, payload: ProductUpdate
    ) -> Product | None:
        """Обновить информацию о товаре."""
        product = await session.get(Product, product_id)
        if product is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for attr, value in update_data.items():
            setattr(product, attr, value)

        if update_data:
            await session.commit()
            await session.refresh(product)
        return product

    @staticmethod
    async def delete_product(session: AsyncSession, product_id: int) -> bool:
        """Удалить товар. Связанные элементы корзины удаляются каскадно."""
        product = await session.get(Product, product_id)
        if product is None:
            return False

        await session.delete(product)
        await session.commit()
        return True
