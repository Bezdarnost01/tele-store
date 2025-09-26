from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from aiogram import Router

from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.select_delivery_method import (
    select_delivery_method_keyboard,
)
from tele_store.states.states import NewDelivery

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)


@router.message(NewDelivery.name)
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
    await state.set_state(NewDelivery.phone_number)
    await message.answer(
        "📞 Теперь укажите номер телефона для связи:",
        reply_markup=cancel_key(),
    )


@router.message(NewDelivery.phone_number)
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
    await state.set_state(NewDelivery.address)
    await message.answer(
        "📍 Укажите адрес доставки или пункт самовывоза:",
        reply_markup=cancel_key(),
    )


@router.message(NewDelivery.address)
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
    await state.set_state(NewDelivery.delivery_method)
    await message.answer(
        "🚚 Какой способ доставки предпочитаете?",
        reply_markup=select_delivery_method_keyboard(),
    )
