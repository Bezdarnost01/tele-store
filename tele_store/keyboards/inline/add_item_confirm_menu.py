from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def add_item_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Добавить", callback_data="add_new_item_confirm"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="add_new_item_cancel"),
    )

    return builder.as_markup()
