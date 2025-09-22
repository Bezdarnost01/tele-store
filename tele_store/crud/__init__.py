"""
Асинхронные CRUD-функции для всех моделей проекта.

Модуль содержит высокоуровневые обёртки над базовыми операциями
SQLAlchemy. Каждая функция принимает экземпляр :class:`AsyncSession`
и возвращает ORM-объекты, полностью подготовленные к дальнейшему
использованию. Все функции снабжены докстрингами и неявно коммитят
изменения, чтобы минимизировать количество шаблонного кода в хендлерах
Telegram-бота.

Функции сгруппированы по доменным моделям и реализуют базовый набор
операций: создание, получение, обновление и удаление (CRUD). Дополнительно
добавлены функции для выборки связанных данных (например, товаров корзины
или заказов пользователя).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.db.enums import OrderStatus
from tele_store.models.models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    User,
)


def _filter_fields(
    allowed: Iterable[str], values: Mapping[str, object]
) -> dict[str, object]:
    """Вернуть только разрешённые поля из входного словаря."""
    allowed_set = set(allowed)
    return {key: value for key, value in values.items() if key in allowed_set}


# --------------------------- Пользователи ---------------------------


async def create_user(
    session: AsyncSession,
    *,
    user_id: int,
    name: str | None = None,
    phone: str | None = None,
    address: str | None = None,
) -> User:
    """
    Создать пользователя.

    ``id`` пользователя совпадает с Telegram ID, поэтому значение
    передаётся явно.
    """
    user = User(id=user_id, name=name, phone=phone, address=address)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Получить пользователя по идентификатору."""
    return await session.get(User, user_id)


async def list_users(
    session: AsyncSession,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[User]:
    """Вернуть список пользователей, упорядоченный по идентификатору."""
    stmt: Select[tuple[User]] = select(User).order_by(User.id).offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession, user_id: int, **fields: object
) -> User | None:
    """
    Обновить данные пользователя.

    Поддерживаются поля ``name``, ``phone`` и ``address``. Если переданы
    другие значения, они будут проигнорированы.
    """
    user = await session.get(User, user_id)
    if user is None:
        return None

    updates = _filter_fields({"name", "phone", "address"}, fields)
    for attr, value in updates.items():
        setattr(user, attr, value)

    if updates:
        await session.commit()
        await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """Удалить пользователя вместе с его корзиной и заказами."""
    user = await session.get(User, user_id)
    if user is None:
        return False

    await session.delete(user)
    await session.commit()
    return True


# --------------------------- Категории ---------------------------


async def create_category(
    session: AsyncSession, *, name: str, description: str | None = None
) -> Category:
    """Создать новую категорию товаров."""
    category = Category(name=name, description=description)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    """Получить категорию по идентификатору."""
    return await session.get(Category, category_id)


async def list_categories(session: AsyncSession) -> list[Category]:
    """Вернуть все категории, отсортированные по имени."""
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def update_category(
    session: AsyncSession, category_id: int, **fields: object
) -> Category | None:
    """Обновить имя или описание категории."""
    category = await session.get(Category, category_id)
    if category is None:
        return None

    updates = _filter_fields({"name", "description"}, fields)
    for attr, value in updates.items():
        setattr(category, attr, value)

    if updates:
        await session.commit()
        await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Удалить категорию вместе со связанными товарами."""
    category = await session.get(Category, category_id)
    if category is None:
        return False

    await session.delete(category)
    await session.commit()
    return True


# --------------------------- Товары ---------------------------


async def create_product(
    session: AsyncSession,
    *,
    category_id: int,
    name: str,
    price: Decimal,
    description: str | None = None,
    photo_file_id: str | None = None,
    is_active: bool = True,
) -> Product:
    """Создать товар и привязать его к категории."""
    product = Product(
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        photo_file_id=photo_file_id,
        is_active=is_active,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    """Получить товар по идентификатору вместе с категорией."""
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.category))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


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


async def update_product(
    session: AsyncSession, product_id: int, **fields: object
) -> Product | None:
    """Обновить информацию о товаре."""
    product = await session.get(Product, product_id)
    if product is None:
        return None

    updates = _filter_fields(
        {
            "category_id",
            "name",
            "description",
            "price",
            "photo_file_id",
            "is_active",
        },
        fields,
    )
    for attr, value in updates.items():
        setattr(product, attr, value)

    if updates:
        await session.commit()
        await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product_id: int) -> bool:
    """Удалить товар. Связанные элементы корзины удаляются каскадно."""
    product = await session.get(Product, product_id)
    if product is None:
        return False

    await session.delete(product)
    await session.commit()
    return True


# --------------------------- Корзины ---------------------------


async def create_cart(session: AsyncSession, *, user_id: int) -> Cart:
    """Создать корзину пользователя."""
    cart = Cart(user_id=user_id)
    session.add(cart)
    await session.commit()
    await session.refresh(cart)
    return cart


async def get_cart(session: AsyncSession, cart_id: int) -> Cart | None:
    """Получить корзину по её идентификатору вместе с товарами."""
    stmt = (
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_cart_by_user(session: AsyncSession, user_id: int) -> Cart | None:
    """Найти корзину пользователя по идентификатору пользователя."""
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_cart(session: AsyncSession, cart_id: int) -> bool:
    """Удалить корзину и связанные элементы."""
    cart = await session.get(Cart, cart_id)
    if cart is None:
        return False

    await session.delete(cart)
    await session.commit()
    return True


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


# --------------------------- Элементы корзины ---------------------------


async def create_cart_item(
    session: AsyncSession,
    *,
    cart_id: int,
    product_id: int,
    quantity: int = 1,
) -> CartItem:
    """Добавить товар в корзину."""
    cart_item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
    session.add(cart_item)
    await session.commit()
    await session.refresh(cart_item)
    return cart_item


async def update_cart_item(
    session: AsyncSession, cart_item_id: int, *, quantity: int | None = None
) -> CartItem | None:
    """Обновить количество товара в корзине."""
    cart_item = await session.get(CartItem, cart_item_id)
    if cart_item is None:
        return None

    if quantity is not None:
        cart_item.quantity = quantity
        await session.commit()
        await session.refresh(cart_item)
    return cart_item


async def delete_cart_item(session: AsyncSession, cart_item_id: int) -> bool:
    """Удалить товар из корзины."""
    cart_item = await session.get(CartItem, cart_item_id)
    if cart_item is None:
        return False

    await session.delete(cart_item)
    await session.commit()
    return True


# --------------------------- Заказы ---------------------------


async def create_order(
    session: AsyncSession,
    *,
    order_number: str,
    user_id: int | None = None,
    total_price: Decimal = Decimal(0),
    delivery_method: str | None = None,
    status: OrderStatus = OrderStatus.NEW,
) -> Order:
    """Создать заказ."""
    order = Order(
        order_number=order_number,
        user_id=user_id,
        total_price=total_price,
        delivery_method=delivery_method,
        status=status,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    """Получить заказ вместе с позициями и данными пользователя."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_orders(
    session: AsyncSession,
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

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_order(
    session: AsyncSession, order_id: int, **fields: object
) -> Order | None:
    """Обновить информацию о заказе."""
    order = await session.get(Order, order_id)
    if order is None:
        return None

    updates = _filter_fields(
        {"order_number", "user_id", "total_price", "delivery_method", "status"},
        fields,
    )
    for attr, value in updates.items():
        setattr(order, attr, value)

    if updates:
        await session.commit()
        await session.refresh(order)
    return order


async def delete_order(session: AsyncSession, order_id: int) -> bool:
    """Удалить заказ и все его позиции."""
    order = await session.get(Order, order_id)
    if order is None:
        return False

    await session.delete(order)
    await session.commit()
    return True


async def count_orders_by_status(
    session: AsyncSession, status: OrderStatus
) -> int:
    """Подсчитать количество заказов в заданном статусе."""
    status_subquery = select(Order.id).where(Order.status == status).subquery()
    stmt = select(func.count()).select_from(status_subquery)
    result = await session.execute(stmt)
    return int(result.scalar_one())


# --------------------------- Позиции заказа ---------------------------


async def create_order_item(
    session: AsyncSession,
    *,
    order_id: int,
    product_id: int,
    quantity: int,
    price: Decimal,
) -> OrderItem:
    """Создать позицию заказа."""
    order_item = OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        price=price,
    )
    session.add(order_item)
    await session.commit()
    await session.refresh(order_item)
    return order_item


async def get_order_item(
    session: AsyncSession, order_item_id: int
) -> OrderItem | None:
    """Получить позицию заказа по идентификатору."""
    return await session.get(OrderItem, order_item_id)


async def list_order_items(session: AsyncSession, order_id: int) -> list[OrderItem]:
    """Получить все позиции конкретного заказа."""
    stmt = (
        select(OrderItem)
        .where(OrderItem.order_id == order_id)
        .options(selectinload(OrderItem.product))
        .order_by(OrderItem.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_order_item(
    session: AsyncSession,
    order_item_id: int,
    **fields: object,
) -> OrderItem | None:
    """Обновить количество или цену позиции заказа."""
    order_item = await session.get(OrderItem, order_item_id)
    if order_item is None:
        return None

    updates = _filter_fields({"quantity", "price"}, fields)
    for attr, value in updates.items():
        setattr(order_item, attr, value)

    if updates:
        await session.commit()
        await session.refresh(order_item)
    return order_item


async def delete_order_item(session: AsyncSession, order_item_id: int) -> bool:
    """Удалить позицию заказа."""
    order_item = await session.get(OrderItem, order_item_id)
    if order_item is None:
        return False

    await session.delete(order_item)
    await session.commit()
    return True
