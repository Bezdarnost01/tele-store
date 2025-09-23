from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from tele_store.models.models import (
    Order,
    OrderItem,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.db.enums import OrderStatus
    from tele_store.schemas.order import (
        CreateOrder,
        CreateOrderItem,
        UpdateOrder,
        UpdateOrderItem,
    )


class OrderManager:
    """Класс для управления заказами пользователей в базе данных"""

    @staticmethod
    async def create_order(
        self: AsyncSession,
        *,
        payload: CreateOrder
    ) -> Order:
        """Создать заказ."""
        order = Order(
            order_number=payload.order_number,
            user_id=payload.user_id,
            total_price=payload.total_price,
            delivery_method=payload.delivery_method,
            status=payload.status,
        )
        self.add(order)
        await self.commit()
        await self.refresh(order)
        return order


    @staticmethod
    async def get_order(self: AsyncSession, order_id: int) -> Order | None:
        """Получить заказ вместе с позициями и данными пользователя."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.user),
            )
        )
        result = await self.execute(stmt)
        return result.scalar_one_or_none()


    @staticmethod
    async def list_orders(
        self: AsyncSession,
        *,
        user_id: int | None = None,
        status: OrderStatus | None = None,
    ) -> list[Order]:
        """Вернуть список заказов с возможностью фильтрации."""
        stmt: Select[tuple[Order]] = select(Order).order_by(Order.created_at.desc())
        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Order.status == status)

        result = await self.execute(stmt)
        return list(result.scalars().all())


    @staticmethod
    async def update_order(
        self: AsyncSession,
        order_id: int,
        payload: UpdateOrder,
    ) -> Order | None:
        """Обновить информацию о заказе."""
        order = await self.get(Order, order_id)
        if order is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for attr, value in updates.items():
            setattr(order, attr, value)

        if updates:
            await self.commit()
            await self.refresh(order)
        return order


    @staticmethod
    async def delete_order(self: AsyncSession, order_id: int) -> bool:
        """Удалить заказ и все его позиции."""
        order = await self.get(Order, order_id)
        if order is None:
            return False

        await self.delete(order)
        await self.commit()
        return True


    @staticmethod
    async def count_orders_by_status(
        self: AsyncSession, status: OrderStatus
    ) -> int:
        """Подсчитать количество заказов в заданном статусе."""
        status_subquery = select(Order.id).where(Order.status == status).subquery()
        stmt = select(func.count()).select_from(status_subquery)
        result = await self.execute(stmt)
        return int(result.scalar_one())


    @staticmethod
    async def create_order_item(
        self: AsyncSession,
        payload: CreateOrderItem,
    ) -> OrderItem:
        """Создать позицию заказа."""
        order_item = OrderItem(
            order_id=payload.order_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            price=payload.price,
        )
        self.add(order_item)
        await self.commit()
        await self.refresh(order_item)
        return order_item


    @staticmethod
    async def get_order_item(
        self: AsyncSession, order_item_id: int
    ) -> OrderItem | None:
        """Получить позицию заказа по идентификатору."""
        return await self.get(OrderItem, order_item_id)


    @staticmethod
    async def list_order_items(self: AsyncSession, order_id: int) -> list[OrderItem]:
        """Получить все позиции конкретного заказа."""
        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .options(selectinload(OrderItem.product))
            .order_by(OrderItem.id)
        )
        result = await self.execute(stmt)
        return list(result.scalars().all())


    @staticmethod
    async def update_order_item(
        self: AsyncSession,
        order_item_id: int,
        payload: UpdateOrderItem,
    ) -> OrderItem | None:
        """Обновить количество или цену позиции заказа."""
        order_item = await self.get(OrderItem, order_item_id)
        if order_item is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for attr, value in updates.items():
            setattr(order_item, attr, value)

        if updates:
            await self.commit()
            await self.refresh(order_item)
        return order_item


    @staticmethod
    async def delete_order_item(self: AsyncSession, order_item_id: int) -> bool:
        """Удалить позицию заказа."""
        order_item = await self.get(OrderItem, order_item_id)
        if order_item is None:
            return False

        await self.delete(order_item)
        await self.commit()
        return True
