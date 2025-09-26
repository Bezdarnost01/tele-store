from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from tele_store.models.models import Cart, CartItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.schemas.cart import AddCartItem, UpdateCartItemCount


class CartManager:
    """Класс для управления корзинами пользователей в базе данных."""

    @staticmethod
    async def create_cart(session: AsyncSession, *, tg_id: int) -> Cart:
        """Создать корзину пользователя."""

        cart = Cart(tg_id=tg_id)
        session.add(cart)
        await session.commit()
        await session.refresh(cart)
        return cart

    @staticmethod
    async def get_cart(session: AsyncSession, cart_id: int) -> Cart | None:
        """Получить корзину по её идентификатору вместе с товарами."""

        stmt = (
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_cart_by_user(session: AsyncSession, tg_id: int) -> Cart | None:
        """Найти корзину пользователя по идентификатору пользователя."""

        stmt = (
            select(Cart)
            .where(Cart.tg_id == tg_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_cart(session: AsyncSession, cart_id: int) -> bool:
        """Удалить корзину и связанные элементы."""

        cart = await session.get(Cart, cart_id)
        if cart is None:
            return False

        await session.delete(cart)
        await session.commit()
        return True

    @staticmethod
    async def list_cart_items(session: AsyncSession, cart_id: int) -> list[CartItem]:
        """Вернуть содержимое корзины."""

        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_cart_item(
        session: AsyncSession, cart_item_id: int
    ) -> CartItem | None:
        """Получить конкретный товар из корзины."""

        stmt = (
            select(CartItem)
            .where(CartItem.id == cart_item_id)
            .options(
                selectinload(CartItem.product), selectinload(CartItem.cart)
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_cart_item_by_product(
        session: AsyncSession, *, cart_id: int, product_id: int
    ) -> CartItem | None:
        """Найти товар в корзине по идентификатору продукта."""

        stmt = (
            select(CartItem)
            .where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
            )
            .options(selectinload(CartItem.product))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def add_cart_item(
        session: AsyncSession, *, payload: AddCartItem
    ) -> CartItem:
        """Добавить товар в корзину."""

        cart_item = CartItem(
            cart_id=payload.cart_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        session.add(cart_item)
        await session.commit()
        await session.refresh(cart_item)
        return cart_item

    @staticmethod
    async def update_cart_item_count(
        session: AsyncSession, payload: UpdateCartItemCount
    ) -> CartItem | None:
        """Обновить количество товара в корзине."""

        cart_item = await session.get(CartItem, payload.cart_item_id)
        if cart_item is None:
            return None

        cart_item.quantity = payload.quantity
        await session.commit()
        await session.refresh(cart_item)
        return cart_item

    @staticmethod
    async def delete_cart_item(session: AsyncSession, cart_item_id: int) -> bool:
        """Удалить товар из корзины."""

        cart_item = await session.get(CartItem, cart_item_id)
        if cart_item is None:
            return False

        await session.delete(cart_item)
        await session.commit()
        return True

    @staticmethod
    async def clear_cart(session: AsyncSession, cart_id: int) -> None:
        """Удалить все товары из корзины."""

        await session.execute(
            delete(CartItem).where(CartItem.cart_id == cart_id)
        )
        await session.commit()
