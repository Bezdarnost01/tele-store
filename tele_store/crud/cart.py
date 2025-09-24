from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from tele_store.models.models import Cart, CartItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.schemas.cart import AddCartItem, UpdateCartItemCount


class CartManager:
    """Класс для управления корзинами пользователей в базе данных"""

    @staticmethod
    async def create_cart(self: AsyncSession, *, tg_id: int) -> Cart:
        """Создать корзину пользователя."""
        cart = Cart(tg_id=tg_id)
        self.add(cart)
        await self.commit()
        await self.refresh(cart)
        return cart

    @staticmethod
    async def get_cart(self: AsyncSession, cart_id: int) -> Cart | None:
        """Получить корзину по её идентификатору вместе с товарами."""
        stmt = (
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await self.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_cart_by_user(self: AsyncSession, tg_id: int) -> Cart | None:
        """Найти корзину пользователя по идентификатору пользователя."""
        stmt = (
            select(Cart)
            .where(Cart.tg_id == tg_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await self.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_cart(self: AsyncSession, cart_id: int) -> bool:
        """Удалить корзину и связанные элементы."""
        cart = await self.get(Cart, cart_id)
        if cart is None:
            return False

        await self.delete(cart)
        await self.commit()
        return True

    @staticmethod
    async def list_cart_items(self: AsyncSession, cart_id: int) -> list[CartItem]:
        """Вернуть содержимое корзины."""
        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.id)
        )
        result = await self.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def add_cart_item(self: AsyncSession, *, payload: AddCartItem) -> CartItem:
        """Добавить товар в корзину."""
        cart_item = CartItem(
            cart_id=payload.cart_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        self.add(cart_item)
        await self.commit()
        await self.refresh(cart_item)
        return cart_item

    @staticmethod
    async def update_cart_item_count(
        self: AsyncSession, payload: UpdateCartItemCount
    ) -> CartItem | None:
        """Обновить количество товара в корзине."""
        cart_item = await self.get(CartItem, payload.cart_item_id)
        if cart_item is None:
            return None

        cart_item.quantity = payload.quantity
        await self.commit()
        await self.refresh(cart_item)
        return cart_item

    @staticmethod
    async def delete_cart_item(self: AsyncSession, cart_item_id: int) -> bool:
        """Удалить товар из корзины."""
        cart_item = await self.get(CartItem, cart_item_id)
        if cart_item is None:
            return False

        await self.delete(cart_item)
        await self.commit()
        return True
