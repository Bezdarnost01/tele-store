from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def item_preview_key(item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить товар", callback_data=f"remove_item:{item_id}"
        )
    )

    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))

    return builder.as_markup()
