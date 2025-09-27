from __future__ import annotations

import logging
import secrets
from decimal import Decimal
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramBadRequest

from tele_store.crud.cart import CartManager
from tele_store.keyboards.inline.cart_menu import build_cart_keyboard

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery
    from sqlalchemy.ext.asyncio import AsyncSession

    from tele_store.models.models import Cart


logger = logging.getLogger(__name__)
MONEY_STEP = Decimal("0.01")


def generate_order_number() -> str:
    """Сгенерировать короткий номер заказа."""
    return secrets.token_hex(4).upper()


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
