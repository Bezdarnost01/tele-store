from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.crud.cart import CartManager
from tele_store.models.models import Category, Product, User
from tele_store.schemas.cart import AddCartItem, UpdateCartItemCount


async def create_user_with_cart(session: AsyncSession, tg_id: int) -> int:
    user = User(tg_id=tg_id)
    session.add(user)
    await session.commit()
    cart = await CartManager.create_cart(session, tg_id=tg_id)
    return cart.id


async def create_product(
    session: AsyncSession, *, category_name: str, product_name: str, price: str
) -> int:
    category = Category(name=category_name, description=None)
    product = Product(
        category=category,
        name=product_name,
        description=None,
        price=Decimal(price),
        photo_file_id=None,
        is_active=True,
    )
    session.add_all([category, product])
    await session.commit()
    return product.id


@pytest.mark.asyncio
async def test_create_cart_for_existing_user(session: AsyncSession) -> None:
    cart_id = await create_user_with_cart(session, tg_id=101)
    assert isinstance(cart_id, int)


@pytest.mark.asyncio
async def test_add_cart_item_and_get_by_product(session: AsyncSession) -> None:
    cart_id = await create_user_with_cart(session, tg_id=202)
    product_id = await create_product(
        session,
        category_name="Категория 202",
        product_name="Товар 202",
        price="15.50",
    )

    payload = AddCartItem(cart_id=cart_id, product_id=product_id, quantity=2)
    cart_item = await CartManager.add_cart_item(session, payload=payload)

    assert cart_item.cart_id == cart_id
    assert cart_item.product_id == product_id
    assert cart_item.quantity == 2

    fetched = await CartManager.get_cart_item_by_product(
        session, cart_id=cart_id, product_id=product_id
    )
    assert fetched is not None
    assert fetched.id == cart_item.id


@pytest.mark.asyncio
async def test_update_cart_item_count_missing_returns_none(
    session: AsyncSession,
) -> None:
    payload = UpdateCartItemCount(cart_item_id=999, quantity=5)
    result = await CartManager.update_cart_item_count(session, payload)
    assert result is None


@pytest.mark.asyncio
async def test_delete_cart_item_missing_returns_false(session: AsyncSession) -> None:
    deleted = await CartManager.delete_cart_item(session, cart_item_id=500)
    assert deleted is False


@pytest.mark.asyncio
async def test_clear_cart_removes_all_items(session: AsyncSession) -> None:
    cart_id = await create_user_with_cart(session, tg_id=303)
    first_product_id = await create_product(
        session,
        category_name="Категория 303-1",
        product_name="Товар 303-1",
        price="20.00",
    )
    second_product_id = await create_product(
        session,
        category_name="Категория 303-2",
        product_name="Товар 303-2",
        price="25.00",
    )

    first_payload = AddCartItem(
        cart_id=cart_id, product_id=first_product_id, quantity=1
    )
    second_payload = AddCartItem(
        cart_id=cart_id, product_id=second_product_id, quantity=3
    )

    await CartManager.add_cart_item(session, payload=first_payload)
    await CartManager.add_cart_item(session, payload=second_payload)

    items_before = await CartManager.list_cart_items(session, cart_id)
    assert len(items_before) == 2

    await CartManager.clear_cart(session, cart_id)

    items_after = await CartManager.list_cart_items(session, cart_id)
    assert items_after == []
