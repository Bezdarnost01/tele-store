from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def select_delivery_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками для выбор типа доставки товара."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🚚 Курьер",
            callback_data="select_courier",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📦 Самовывоз",
            callback_data="select_self-delivery",
        )
    )

    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))

    return builder.as_markup()
