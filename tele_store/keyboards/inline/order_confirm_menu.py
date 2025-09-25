from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def order_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения оформления заказа."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data="confirm_order",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="cancel_order",
        )
    )

    return builder.as_markup()
