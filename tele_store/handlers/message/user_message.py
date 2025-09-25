from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Router

from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.order_confirm_menu import order_confirm_keyboard
from tele_store.states.states import RegNewUser

if TYPE_CHECKING:
    from decimal import Decimal

router = Router()
logger = logging.getLogger(__name__)


@router.message(RegNewUser.name)
async def process_order_name(message: Message, state: FSMContext) -> None:
    """Запросить имя покупателя."""

    name = message.text.strip()
    if not name:
        await message.answer(
            "❌ Имя не может быть пустым. Введите его ещё раз:",
            reply_markup=cancel_key(),
        )
        return

    await state.update_data(name=name)
    await state.set_state(RegNewUser.phone_number)
    await message.answer(
        "📞 Теперь укажите номер телефона для связи:",
        reply_markup=cancel_key(),
    )


@router.message(RegNewUser.phone_number)
async def process_order_phone(message: Message, state: FSMContext) -> None:
    """Получить контактный номер пользователя."""

    raw_phone = message.text.strip()
    digits_only = re.sub(r"\D", "", raw_phone)

    if len(digits_only) < 10 or len(digits_only) > 15:
        await message.answer(
            "❌ Похоже, номер введён неверно. Попробуйте снова в формате +79991234567:",
            reply_markup=cancel_key(),
        )
        return

    await state.update_data(phone_number=raw_phone)
    await state.set_state(RegNewUser.address)
    await message.answer(
        "📍 Укажите адрес доставки или пункт самовывоза:",
        reply_markup=cancel_key(),
    )


@router.message(RegNewUser.address)
async def process_order_address(message: Message, state: FSMContext) -> None:
    """Сохранить адрес доставки пользователя."""

    address = message.text.strip()
    if not address:
        await message.answer(
            "❌ Адрес не может быть пустым. Напишите его полностью:",
            reply_markup=cancel_key(),
        )
        return

    await state.update_data(address=address)
    await state.set_state(RegNewUser.delivery_method)
    await message.answer(
        "🚚 Какой способ доставки предпочитаете?", reply_markup=cancel_key()
    )


@router.message(RegNewUser.delivery_method)
async def process_delivery_method(message: Message, state: FSMContext) -> None:
    """Получить желаемый метод доставки."""

    delivery_method = message.text.strip()
    if not delivery_method:
        await message.answer(
            "❌ Нужно указать способ доставки. Например: курьером или самовывоз.",
            reply_markup=cancel_key(),
        )
        return

    await state.update_data(delivery_method=delivery_method)
    await state.set_state(RegNewUser.confirm)

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

    await message.answer(preview, reply_markup=order_confirm_keyboard())
