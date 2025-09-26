from __future__ import annotations

import logging
import secrets
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from tele_store.crud.category import CategoryManager
from tele_store.crud.order import OrderManager
from tele_store.crud.product import ProductManager
from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.product_order_menu import product_order_keyboard
from tele_store.keyboards.inline.user_category_menu import get_user_category_keyboard
from tele_store.keyboards.inline.user_product_menu import get_user_product_keyboard
from tele_store.keyboards.inline.order_confirm_menu import order_confirm_keyboard
from tele_store.schemas.order import CreateOrder, CreateOrderItem
from tele_store.states.states import NewDelivery

if TYPE_CHECKING:
    from decimal import Decimal
    from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
logger = logging.getLogger(__name__)


def generate_order_number() -> str:
    """Сгенерировать короткий номер заказа."""

    return secrets.token_hex(4).upper()


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

    category = await CategoryManager.get_category(session=session, category_id=category_id)

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
async def open_cart(call: CallbackQuery) -> None:
    """Сообщить пользователю о временном отсутствии корзины."""

    await call.answer("Корзина будет доступна позже.", show_alert=True)


@router.callback_query(F.data == "cancel_order")
async def cancel_order(call: CallbackQuery, state: FSMContext) -> None:
    """Отменить оформление заказа на этапе подтверждения."""

    if await state.get_state() == NewDelivery.confirm.state:
        await state.clear()
    await call.message.edit_text("❌ Оформление заказа отменено.")
    await call.answer()


@router.callback_query(F.data.startswith("order_product:"))
async def start_order(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Запустить процесс оформления заказа для выбранного товара."""

    product_id = int(call.data.split(":")[1])
    product = await ProductManager.get_product(session=session, product_id=product_id)

    if product is None or not product.is_active:
        await call.answer("Товар недоступен для заказа.", show_alert=True)
        return

    await state.clear()
    await state.set_state(NewDelivery.name)
    await state.update_data(
        product_id=product.id,
        product_name=product.name,
        product_price=str(product.price),
    )

    await call.message.answer(
        "Отличный выбор! Давай оформим заказ. Как к тебе обращаться?",
        reply_markup=cancel_key(),
    )
    await call.answer()

@router.callback_query(
    NewDelivery.delivery_method,
    F.data.in_(["select_courier", "select_self-delivery"])
)
async def confirm_order(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Получить желаемый метод доставки."""

    delivery_method = (
        "Курьер" if call.data == "select_courier" else "Самовывоз"
    )

    if not delivery_method:
        await call.message.answer(
            "❌ Нужно указать способ доставки. Например: курьером или самовывоз.",
            reply_markup=cancel_key(),
        )
        return

    await state.update_data(delivery_method=delivery_method)
    await state.set_state(NewDelivery.confirm)
    await call.answer()

    data = await state.get_data()
    product_name = data.get("product_name", "—")
    product_price: Decimal | str | None = data.get("product_price")
    price_text = str(product_price) if product_price is not None else "—"

    preview = (
        "📦 <b>Проверьте данные заказа</b>\n\n"
        f"Товар: {product_name}\n"
        f"Стоимость: {price_text} ₽\n\n"
        f"Имя: {data.get('name')}\n"
        f"Телефон: {data.get('phone_number')}\n"
        f"Адрес: {data.get('address')}\n"
        f"Доставка: {delivery_method}\n\n"
        "Если всё верно — подтвердите оформление."
    )

    await call.message.answer(preview, reply_markup=order_confirm_keyboard())

@router.callback_query(NewDelivery.confirm, F.data == "confirm_order")
async def confirm_order(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Подтвердить заказ и сохранить его в базе."""

    data = await state.get_data()
    product_id_raw = data.get("product_id")
    if product_id_raw is None:
        await state.clear()
        await call.message.edit_text(
            "❌ Не удалось оформить заказ. Попробуйте выбрать товар ещё раз."
        )
        await call.answer(show_alert=True)
        return

    product_id = int(product_id_raw)
    product = await ProductManager.get_product(session=session, product_id=product_id)

    if product is None or not product.is_active:
        await state.clear()
        await call.message.edit_text(
            "❌ Не удалось оформить заказ: выбранный товар больше недоступен."
        )
        await call.answer(show_alert=True)
        return

    order_number = generate_order_number()
    price: Decimal = product.price

    order_payload = CreateOrder(
        order_number=order_number,
        tg_id=call.from_user.id,
        total_price=price,
        delivery_method=data.get("delivery_method"),
    )

    order = await OrderManager.create_order(session=session, payload=order_payload)

    order_item_payload = CreateOrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        price=price,
    )

    await OrderManager.create_order_item(session=session, payload=order_item_payload)

    summary = (
        "✅ <b>Заказ оформлен!</b>\n\n"
        f"Номер заказа: <code>{order_number}</code>\n"
        f"Товар: {product.name}\n"
        f"Стоимость: {price} ₽\n\n"
        f"Имя: {data.get('name')}\n"
        f"Телефон: {data.get('phone_number')}\n"
        f"Адрес: {data.get('address')}\n"
        f"Доставка: {data.get('delivery_method')}\n\n"
        "Мы свяжемся с вами в ближайшее время для уточнения деталей."
    )

    await call.message.edit_text(summary)
    await state.clear()
    await call.answer("Заказ успешно создан!", show_alert=True)
