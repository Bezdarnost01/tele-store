"""Тесты, проверяющие CRUD-операции для всех моделей проекта."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from tele_store import crud
from tele_store.db.enums import OrderStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_user_crud(session: AsyncSession) -> None:
    user = await crud.create_user(session, user_id=123, name="Alice")
    assert user.id == 123
    assert user.name == "Alice"

    fetched = await crud.get_user(session, user.id)
    assert fetched is not None
    assert fetched.phone is None

    updated = await crud.update_user(
        session, user.id, phone="+100200", address="Main street, 1"
    )
    assert updated is not None
    assert updated.phone == "+100200"
    assert updated.address == "Main street, 1"

    missing_update = await crud.update_user(session, 999, name="Ghost")
    assert missing_update is None

    users = await crud.list_users(session)
    assert [u.id for u in users] == [123]

    assert await crud.delete_user(session, user.id) is True
    assert await crud.delete_user(session, user.id) is False


@pytest.mark.asyncio
async def test_category_and_product_crud(session: AsyncSession) -> None:
    category = await crud.create_category(
        session, name="Electronics", description="Devices and gadgets"
    )
    assert category.id is not None

    product = await crud.create_product(
        session,
        category_id=category.id,
        name="Smartphone",
        description="OLED display",
        price=Decimal("499.90"),
        photo_file_id="photo_1",
    )
    assert product.category_id == category.id

    categories = await crud.list_categories(session)
    assert len(categories) == 1

    fetched = await crud.get_product(session, product.id)
    assert fetched is not None
    assert fetched.category.id == category.id

    updated_product = await crud.update_product(
        session,
        product.id,
        price=Decimal("450.00"),
        is_active=False,
    )
    assert updated_product is not None
    assert updated_product.price == Decimal("450.00")
    assert updated_product.is_active is False

    active_products = await crud.list_products(session)
    assert active_products == []

    all_products = await crud.list_products(session, only_active=False)
    assert [p.id for p in all_products] == [product.id]

    assert await crud.delete_product(session, product.id) is True
    assert await crud.delete_product(session, product.id) is False

    assert await crud.delete_category(session, category.id) is True
    assert await crud.delete_category(session, category.id) is False


@pytest.mark.asyncio
async def test_cart_crud(session: AsyncSession) -> None:
    user = await crud.create_user(session, user_id=555, name="Bob")
    category = await crud.create_category(session, name="Books")
    product = await crud.create_product(
        session, category_id=category.id, name="Novel", price=Decimal("12.50")
    )

    cart = await crud.create_cart(session, user_id=user.id)
    assert cart.user_id == user.id

    cart_item = await crud.create_cart_item(
        session, cart_id=cart.id, product_id=product.id, quantity=2
    )
    assert cart_item.quantity == 2

    items = await crud.list_cart_items(session, cart.id)
    assert len(items) == 1

    updated_item = await crud.update_cart_item(session, cart_item.id, quantity=5)
    assert updated_item is not None
    assert updated_item.quantity == 5

    fetched_cart = await crud.get_cart(session, cart.id)
    assert fetched_cart is not None
    assert len(fetched_cart.items) == 1

    fetched_by_user = await crud.get_cart_by_user(session, user.id)
    assert fetched_by_user is not None
    assert fetched_by_user.id == cart.id

    assert await crud.delete_cart_item(session, cart_item.id) is True
    assert await crud.delete_cart_item(session, cart_item.id) is False

    assert await crud.delete_cart(session, cart.id) is True
    assert await crud.delete_cart(session, cart.id) is False


@pytest.mark.asyncio
async def test_order_crud(session: AsyncSession) -> None:
    user = await crud.create_user(session, user_id=777, name="Charlie")
    category = await crud.create_category(session, name="Accessories")
    product = await crud.create_product(
        session,
        category_id=category.id,
        name="Watch",
        price=Decimal("199.99"),
    )

    order = await crud.create_order(
        session,
        order_number="ORD-001",
        user_id=user.id,
        total_price=Decimal("199.99"),
        delivery_method="courier",
    )
    assert order.status == OrderStatus.NEW

    order_item = await crud.create_order_item(
        session,
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        price=Decimal("199.99"),
    )
    assert order_item.price == Decimal("199.99")

    items = await crud.list_order_items(session, order.id)
    assert len(items) == 1

    await crud.update_order_item(session, order_item.id, quantity=3)
    updated_order_item = await crud.get_order_item(session, order_item.id)
    assert updated_order_item is not None
    assert updated_order_item.quantity == 3

    await crud.update_order(session, order.id, status=OrderStatus.PROCESSING)
    processing_orders = await crud.list_orders(session, status=OrderStatus.PROCESSING)
    assert [o.id for o in processing_orders] == [order.id]

    counter = await crud.count_orders_by_status(session, OrderStatus.PROCESSING)
    assert counter == 1

    fetched_order = await crud.get_order(session, order.id)
    assert fetched_order is not None
    assert len(fetched_order.items) == 1
    assert fetched_order.user.id == user.id

    assert await crud.delete_order_item(session, order_item.id) is True
    assert await crud.delete_order_item(session, order_item.id) is False

    assert await crud.delete_order(session, order.id) is True
    assert await crud.delete_order(session, order.id) is False
