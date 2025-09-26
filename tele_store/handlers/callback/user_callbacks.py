from __future__ import annotations

import logging
import secrets
from decimal import Decimal
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest

from tele_store.crud.cart import CartManager
from tele_store.crud.category import CategoryManager
from tele_store.crud.order import OrderManager
from tele_store.crud.product import ProductManager
from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.cart_menu import build_cart_keyboard
from tele_store.keyboards.inline.order_confirm_menu import order_confirm_keyboard
from tele_store.keyboards.inline.product_order_menu import product_order_keyboard
from tele_store.keyboards.inline.user_category_menu import get_user_category_keyboard
from tele_store.keyboards.inline.user_product_menu import get_user_product_keyboard
from tele_store.schemas.cart import AddCartItem, UpdateCartItemCount
from tele_store.schemas.order import CreateOrder, CreateOrderItem
from tele_store.states.states import NewDelivery

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.models.models import Cart

router = Router()
logger = logging.getLogger(__name__)


def generate_order_number() -> str:
    """Сгенерировать короткий номер заказа."""
    return secrets.token_hex(4).upper()


MONEY_STEP = Decimal("0.01")


def format_money(amount: Decimal) -> str:
    """Отформатировать цену для отображения пользователю."""
    return f"{amount.quantize(MONEY_STEP)} ₽"


def collect_cart_lines(cart: Cart) -> tuple[list[str], Decimal]:
    """Собрать список строк с содержимым корзины и подсчитать сумму."""
    total = Decimal(0)
    lines: list[str] = []

    for index, item in enumerate(cart.items, start=1):
        product = item.product
        if product is None:
            continue

        line_total = product.price * item.quantity
        total += line_total
        lines.append(
            f"{index}. {product.name} — {item.quantity} шт. × "
            f"{format_money(product.price)} = {format_money(line_total)}"
        )

    return lines, total


def build_cart_text(cart: Cart) -> str:
    """Подготовить текстовое представление корзины."""
    lines, total = collect_cart_lines(cart)
    if not lines:
        return "🛒 Сейчас ваша корзина пуста."

    items_text = "\n".join(lines)
    return (
        "🛒 <b>Ваша корзина</b>\n\n"
        f"{items_text}\n\n"
        f"Итого: <b>{format_money(total)}</b>\n"
        "Используйте кнопки ниже, чтобы изменить корзину или оформить заказ."
    )


def build_order_preview_text(cart: Cart, data: dict[str, object]) -> str:
    """Сформировать текст подтверждения заказа."""
    lines, total = collect_cart_lines(cart)
    items_text = "\n".join(lines) if lines else "Корзина пуста"

    return (
        "📦 <b>Проверьте данные заказа</b>\n\n"
        f"{items_text}\n\n"
        f"Итого: <b>{format_money(total)}</b>\n\n"
        f"Имя: {data.get('name', '—')}\n"
        f"Телефон: {data.get('phone_number', '—')}\n"
        f"Адрес: {data.get('address', '—')}\n"
        f"Доставка: {data.get('delivery_method', '—')}\n\n"
        "Если всё верно — подтвердите оформление."
    )


async def sanitize_cart(session: AsyncSession, cart: Cart) -> Cart | None:
    """Удалить из корзины недоступные товары и вернуть актуальную корзину."""
    removed = False
    for item in list(cart.items):
        product = item.product
        if product is None or not getattr(product, "is_active", True):
            await CartManager.delete_cart_item(session, item.id)
            removed = True

    if removed:
        return await CartManager.get_cart_by_user(session=session, tg_id=cart.tg_id)
    return cart


async def refresh_cart_view(call: CallbackQuery, session: AsyncSession) -> Cart | None:
    """Перерисовать сообщение с корзиной."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None:
        try:
            await call.message.edit_text("🛒 Сейчас ваша корзина пуста.")
        except TelegramBadRequest:
            logger.debug("Не удалось обновить сообщение корзины", exc_info=True)
        return None

    cart = await sanitize_cart(session, cart) or cart
    if not cart.items:
        try:
            await call.message.edit_text("🛒 Сейчас ваша корзина пуста.")
        except TelegramBadRequest:
            logger.debug("Не удалось обновить сообщение корзины", exc_info=True)
        return None

    text = build_cart_text(cart)
    keyboard = build_cart_keyboard(cart)
    try:
        await call.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        logger.debug("Не удалось обновить сообщение корзины", exc_info=True)

    return cart


@router.callback_query(F.data == "catalog")
async def open_catalog(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать пользователю список категорий."""
    keyboard, total = await get_user_category_keyboard(session=session)

    if total == 0:
        await call.answer("Категории пока не добавлены.", show_alert=True)
        return

    await call.answer()
    await call.message.answer("📂 Выберите категорию:", reply_markup=keyboard)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(call: CallbackQuery, session: AsyncSession) -> None:
    """Вернуться к списку категорий."""
    keyboard, total = await get_user_category_keyboard(session=session)

    if total == 0:
        await call.answer("Категории пока недоступны.", show_alert=True)
        return

    await call.answer()

    try:
        await call.message.edit_reply_markup()
    except Exception:
        logger.debug("Не удалось очистить клавиатуру сообщения", exc_info=True)

    await call.message.answer("📂 Выберите категорию:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("user_category_page:"))
async def paginate_categories(call: CallbackQuery, session: AsyncSession) -> None:
    """Переключение страниц списка категорий."""
    page = int(call.data.split(":")[1])
    keyboard, total = await get_user_category_keyboard(session=session, page=page)

    if total == 0:
        await call.answer("Категории пока отсутствуют.", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("user_category:"))
async def open_category(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать товары выбранной категории."""
    _, category_id_raw, *_ = call.data.split(":")
    category_id = int(category_id_raw)

    category = await CategoryManager.get_category(
        session=session, category_id=category_id
    )

    if category is None:
        await call.answer("Категория не найдена.", show_alert=True)
        return

    keyboard, total = await get_user_product_keyboard(
        session=session, category_id=category_id
    )

    if total == 0:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    await call.answer()
    await call.message.answer(
        f"🛍 <b>{category.name}</b>\nВыберите товар для оформления заказа:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("user_product_page:"))
async def paginate_products(call: CallbackQuery, session: AsyncSession) -> None:
    """Переключение страниц товаров внутри категории."""
    _, category_raw, page_raw = call.data.split(":")
    category_id = int(category_raw)
    page = int(page_raw)

    keyboard, total = await get_user_product_keyboard(
        session=session, category_id=category_id, page=page
    )

    if total == 0:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("user_product:"))
async def show_product_preview(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать карточку товара с предложением оформить заказ."""
    _, product_raw, category_raw, page_raw = call.data.split(":")
    product_id = int(product_raw)
    category_id = int(category_raw)
    page = int(page_raw)

    product = await ProductManager.get_product(session=session, product_id=product_id)

    if product is None or not product.is_active:
        await call.answer("Товар недоступен.", show_alert=True)
        return

    caption = (
        f"📦 <b>{product.name}</b>\n"
        f"💵 Цена: {product.price} ₽\n"
        f"📜 Описание: {product.description or '—'}"
    )

    keyboard = product_order_keyboard(
        category_id=category_id, product_id=product.id, page=page
    )

    if product.photo_file_id:
        await call.message.answer_photo(
            product.photo_file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    else:
        await call.message.answer(caption, reply_markup=keyboard)

    await call.answer()


@router.callback_query(F.data == "cart")
async def open_cart(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать пользователю содержимое корзины."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    cleaned_cart = await sanitize_cart(session, cart) if cart else cart

    if cleaned_cart is None or not cleaned_cart.items:
        await call.answer("Сейчас корзина пуста.", show_alert=True)
        return

    if cleaned_cart is not cart:
        await call.answer(
            "Некоторые товары больше недоступны и были убраны из корзины.",
            show_alert=True,
        )
    else:
        await call.answer()

    text = build_cart_text(cleaned_cart)
    keyboard = build_cart_keyboard(cleaned_cart)
    await call.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cancel_order")
async def cancel_order(call: CallbackQuery, state: FSMContext) -> None:
    """Отменить оформление заказа и очистить состояние."""
    if await state.get_state() is not None:
        await state.clear()
    try:
        await call.message.edit_text(
            "❌ Оформление заказа отменено. Корзина сохранена, можно продолжить покупки."
        )
    except TelegramBadRequest:
        logger.debug("Не удалось обновить сообщение при отмене заказа", exc_info=True)
    await call.answer()


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_product_to_cart(call: CallbackQuery, session: AsyncSession) -> None:
    """Добавить выбранный товар в корзину пользователя."""
    product_id = int(call.data.split(":")[1])
    product = await ProductManager.get_product(session=session, product_id=product_id)

    if product is None or not product.is_active:
        await call.answer("Товар недоступен для добавления.", show_alert=True)
        return

    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None:
        cart = await CartManager.create_cart(session=session, tg_id=call.from_user.id)

    existing_item = await CartManager.get_cart_item_by_product(
        session=session, cart_id=cart.id, product_id=product.id
    )

    if existing_item is None:
        await CartManager.add_cart_item(
            session=session,
            payload=AddCartItem(cart_id=cart.id, product_id=product.id, quantity=1),
        )
    else:
        await CartManager.update_cart_item_count(
            session=session,
            payload=UpdateCartItemCount(
                cart_item_id=existing_item.id,
                quantity=existing_item.quantity + 1,
            ),
        )

    await call.answer("Добавлено в корзину!")


@router.callback_query(F.data.startswith("cart_increase:"))
async def increase_cart_item(call: CallbackQuery, session: AsyncSession) -> None:
    """Увеличить количество товара в корзине."""
    item_id = int(call.data.split(":")[1])
    cart_item = await CartManager.get_cart_item(session=session, cart_item_id=item_id)

    if cart_item is None or cart_item.cart.tg_id != call.from_user.id:
        await call.answer("Товар не найден в корзине.", show_alert=True)
        return

    await CartManager.update_cart_item_count(
        session=session,
        payload=UpdateCartItemCount(
            cart_item_id=cart_item.id,
            quantity=cart_item.quantity + 1,
        ),
    )

    await refresh_cart_view(call, session)
    await call.answer("Количество увеличено.")


@router.callback_query(F.data.startswith("cart_decrease:"))
async def decrease_cart_item(call: CallbackQuery, session: AsyncSession) -> None:
    """Уменьшить количество товара в корзине."""
    item_id = int(call.data.split(":")[1])
    cart_item = await CartManager.get_cart_item(session=session, cart_item_id=item_id)

    if cart_item is None or cart_item.cart.tg_id != call.from_user.id:
        await call.answer("Товар не найден в корзине.", show_alert=True)
        return

    new_quantity = cart_item.quantity - 1
    if new_quantity <= 0:
        await CartManager.delete_cart_item(session=session, cart_item_id=cart_item.id)
        await refresh_cart_view(call, session)
        await call.answer("Товар удалён из корзины.")
        return

    await CartManager.update_cart_item_count(
        session=session,
        payload=UpdateCartItemCount(
            cart_item_id=cart_item.id,
            quantity=new_quantity,
        ),
    )

    await refresh_cart_view(call, session)
    await call.answer("Количество уменьшено.")


@router.callback_query(F.data.startswith("cart_remove:"))
async def remove_cart_item(call: CallbackQuery, session: AsyncSession) -> None:
    """Удалить выбранный товар из корзины."""
    item_id = int(call.data.split(":")[1])
    cart_item = await CartManager.get_cart_item(session=session, cart_item_id=item_id)

    if cart_item is None or cart_item.cart.tg_id != call.from_user.id:
        await call.answer("Товар уже отсутствует в корзине.", show_alert=True)
        return

    await CartManager.delete_cart_item(session=session, cart_item_id=cart_item.id)
    await refresh_cart_view(call, session)
    await call.answer("Товар удалён.")


@router.callback_query(F.data == "cart_clear")
async def clear_cart(call: CallbackQuery, session: AsyncSession) -> None:
    """Полностью очистить корзину пользователя."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None or not cart.items:
        await call.answer("Корзина уже пуста.", show_alert=True)
        return

    await CartManager.clear_cart(session=session, cart_id=cart.id)
    await refresh_cart_view(call, session)
    await call.answer("Корзина очищена.")


@router.callback_query(F.data.startswith("cart_ignore:"))
async def ignore_cart_info(call: CallbackQuery) -> None:
    """Обработать нажатие на неактивную кнопку количества."""
    await call.answer()


@router.callback_query(F.data == "checkout_cart")
async def start_checkout(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Запустить процесс оформления заказа из корзины."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None or not cart.items:
        await call.answer(
            "Корзина пуста. Добавьте товары перед оформлением.", show_alert=True
        )
        await refresh_cart_view(call, session)
        return

    cleaned_cart = await sanitize_cart(session, cart) or cart
    if cleaned_cart is None or not cleaned_cart.items:
        await call.answer(
            "В корзине не осталось доступных товаров. Добавьте новые позиции.",
            show_alert=True,
        )
        await refresh_cart_view(call, session)
        return

    await state.clear()
    await state.set_state(NewDelivery.name)
    await state.update_data(cart_id=cleaned_cart.id)

    await call.answer()
    try:
        await call.message.edit_text(
            "Отличный выбор! Давай оформим заказ. Как к тебе обращаться?",
            reply_markup=cancel_key(),
        )
    except TelegramBadRequest:
        logger.debug(
            "Не удалось обновить сообщение корзины перед оформлением", exc_info=True
        )
        await call.message.answer(
            "Отличный выбор! Давай оформим заказ. Как к тебе обращаться?",
            reply_markup=cancel_key(),
        )


@router.callback_query(
    NewDelivery.delivery_method, F.data.in_(["select_courier", "select_self-delivery"])
)
async def choose_delivery_method(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Получить желаемый способ доставки перед подтверждением заказа."""
    delivery_method = "Курьер" if call.data == "select_courier" else "Самовывоз"

    await state.update_data(delivery_method=delivery_method)
    await state.set_state(NewDelivery.confirm)

    data = await state.get_data()
    cart_id = data.get("cart_id")

    if cart_id is None:
        await state.clear()
        await call.message.answer(
            "❌ Корзина не найдена. Попробуйте начать оформление заново.",
            reply_markup=cancel_key(),
        )
        await call.answer(show_alert=True)
        return

    cart = await CartManager.get_cart(session=session, cart_id=int(cart_id))
    cart = await sanitize_cart(session, cart) if cart else cart

    if cart is None or not cart.items:
        await state.clear()
        await call.message.answer(
            "❌ Корзина пуста. Добавьте товары и начните оформление заново.",
        )
        await call.answer(show_alert=True)
        return

    preview = build_order_preview_text(cart, data)
    await call.answer()
    await call.message.answer(preview, reply_markup=order_confirm_keyboard())


@router.callback_query(NewDelivery.confirm, F.data == "confirm_order")
async def confirm_order(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Подтвердить заказ из корзины и сохранить его в базе."""
    data = await state.get_data()
    cart_id = data.get("cart_id")

    if cart_id is None:
        await state.clear()
        await call.message.edit_text(
            "❌ Не удалось найти корзину. Попробуйте оформить заказ заново."
        )
        await call.answer(show_alert=True)
        return

    cart = await CartManager.get_cart(session=session, cart_id=int(cart_id))
    cart = await sanitize_cart(session, cart) if cart else cart

    if cart is None or not cart.items:
        await state.clear()
        await call.message.edit_text(
            "❌ Корзина пуста. Добавьте товары и попробуйте снова."
        )
        await call.answer(show_alert=True)
        return

    lines, total_price = collect_cart_lines(cart)
    if not lines:
        await state.clear()
        await call.message.edit_text(
            "❌ В корзине нет доступных товаров. Попробуйте добавить новые позиции."
        )
        await call.answer(show_alert=True)
        return

    order_number = generate_order_number()
    order_payload = CreateOrder(
        order_number=order_number,
        tg_id=call.from_user.id,
        name=data.get("name"),
        phone=data.get("phone_number"),
        addres=data.get("address"),
        total_price=total_price,
        delivery_method=data.get("delivery_method"),
    )

    order = await OrderManager.create_order(session=session, payload=order_payload)

    for item in cart.items:
        product = item.product
        if product is None:
            continue
        await OrderManager.create_order_item(
            session=session,
            payload=CreateOrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price,
            ),
        )

    await CartManager.clear_cart(session=session, cart_id=cart.id)

    items_text = "\n".join(lines)
    summary = (
        "✅ <b>Заказ оформлен!</b>\n\n"
        f"Номер заказа: <code>{order_number}</code>\n"
        f"{items_text}\n\n"
        f"Итого: <b>{format_money(total_price)}</b>\n\n"
        f"Имя: {data.get('name')}\n"
        f"Телефон: {data.get('phone_number')}\n"
        f"Адрес: {data.get('address')}\n"
        f"Доставка: {data.get('delivery_method')}\n\n"
        "Мы свяжемся с вами в ближайшее время для уточнения деталей."
    )

    await call.message.edit_text(summary)
    await state.clear()
    await call.answer("Заказ успешно создан!", show_alert=True)
