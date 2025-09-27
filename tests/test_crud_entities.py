from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.crud.category import CategoryManager
from tele_store.crud.order import OrderManager
from tele_store.crud.product import ProductManager
from tele_store.crud.user import UserManager
from tele_store.db.enums import OrderStatus
from tele_store.schemas.order import (
    CreateOrder,
    CreateOrderItem,
    UpdateOrder,
    UpdateOrderItem,
)
from tele_store.schemas.product import CreateProduct, ProductUpdate


@pytest.mark.asyncio
async def test_user_manager_crud(session: AsyncSession) -> None:
    user = await UserManager.create_user(session=session, tg_id=555)

    fetched = await UserManager.get_user(session=session, tg_id=555)
    assert fetched is not None
    assert fetched.id == user.id

    users = await UserManager.list_users(session=session)
    assert any(u.tg_id == 555 for u in users)

    deleted = await UserManager.delete_user(session=session, user_id=user.id)
    assert deleted is True
    assert await UserManager.get_user(session=session, tg_id=555) is None


@pytest.mark.asyncio
async def test_category_and_product_crud(session: AsyncSession) -> None:
    category = await CategoryManager.create_category(
        session=session, name="Электроника", description="Гаджеты"
    )

    categories = await CategoryManager.list_categories(session=session)
    assert any(cat.id == category.id for cat in categories)

    await CategoryManager.update_category(
        session=session,
        category_id=category.id,
        description="Устройства и аксессуары",
    )

    product = await ProductManager.create_product(
        session=session,
        payload=CreateProduct(
            category_id=category.id,
            name="Смартфон",
            description="Флагманская модель",
            price=Decimal("49990.00"),
        ),
    )

    fetched_product = await ProductManager.get_product(session=session, product_id=product.id)
    assert fetched_product is not None
    assert fetched_product.name == "Смартфон"

    products = await ProductManager.list_products(session=session, category_id=category.id)
    assert len(products) == 1

    updated_product = await ProductManager.update_product(
        session=session,
        product_id=product.id,
        payload=ProductUpdate(name="Смартфон X", price=Decimal("45990.00")),
    )
    assert updated_product is not None
    assert updated_product.name == "Смартфон X"
    assert updated_product.price == Decimal("45990.00")

    deleted_product = await ProductManager.delete_product(session=session, product_id=product.id)
    assert deleted_product is True


@pytest.mark.asyncio
async def test_order_manager_flow(session: AsyncSession) -> None:
    user = await UserManager.create_user(session=session, tg_id=777)
    category = await CategoryManager.create_category(session=session, name="Игрушки")
    product = await ProductManager.create_product(
        session=session,
        payload=CreateProduct(
            category_id=category.id,
            name="Конструктор",
            price=Decimal("1990.50"),
        ),
    )

    order = await OrderManager.create_order(
        session=session,
        payload=CreateOrder(
            order_number="ORD-777",
            tg_id=user.tg_id,
            name="Иван",
            phone="+79991234567",
            address="Москва, Тверская 1",
            total_price=Decimal("1990.50"),
            delivery_method="Курьер",
        ),
    )

    orders_for_user = await OrderManager.list_orders(session=session, tg_id=user.tg_id)
    assert len(orders_for_user) == 1

    order_item = await OrderManager.create_order_item(
        session=session,
        payload=CreateOrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            price=product.price,
        ),
    )

    items = await OrderManager.list_order_items(session=session, order_id=order.id)
    assert len(items) == 1
    assert items[0].id == order_item.id

    updated_order = await OrderManager.update_order(
        session=session,
        order_id=order.id,
        payload=UpdateOrder(
            status=OrderStatus.PROCESSING,
            total_price=Decimal("3981.00"),
            address="Москва, Тверская 1, офис 2",
        ),
    )
    assert updated_order is not None
    assert updated_order.status == OrderStatus.PROCESSING
    assert updated_order.address.endswith("офис 2")

    await OrderManager.update_order_item(
        session=session,
        order_item_id=order_item.id,
        payload=UpdateOrderItem(quantity=2),
    )

    processing_count = await OrderManager.count_orders_by_status(
        session=session, status=OrderStatus.PROCESSING
    )
    assert processing_count == 1

    deleted_item = await OrderManager.delete_order_item(session=session, order_item_id=order_item.id)
    assert deleted_item is True

    deleted_order = await OrderManager.delete_order(session=session, order_id=order.id)
    assert deleted_order is True

    remaining_orders = await OrderManager.list_orders(session=session, tg_id=user.tg_id)
    assert remaining_orders == []
