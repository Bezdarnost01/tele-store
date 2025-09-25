from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📜 Каталог", 
            callback_data="catalog"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🛒 Корзина",
            callback_data="cart",
        )
    )

    return builder.as_markup()
