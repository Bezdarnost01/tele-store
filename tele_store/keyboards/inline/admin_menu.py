from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_new_item")
    )
    builder.row(
        InlineKeyboardButton(
            text="📦 Список товаров:",
            callback_data="item_list",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📜 Список заказов",
            callback_data="orders_list",
        )
    )

    return builder.as_markup()
