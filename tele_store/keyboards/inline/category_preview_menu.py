from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def category_preview_key(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить категорию", callback_data=f"remove_category:{category_id}"
        )
    )

    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))

    return builder.as_markup()
