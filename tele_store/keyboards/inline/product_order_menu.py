from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def product_order_keyboard(
    *,
    category_id: int,
    product_id: int,
    page: int,
) -> InlineKeyboardMarkup:
    """Клавиатура с кнопками для оформления заказа товара."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить в корзину",
            callback_data=f"add_to_cart:{product_id}",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🛒 Перейти в корзину",
            callback_data="cart",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к списку",
            callback_data=f"user_product_page:{category_id}:{page}",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ К категориям",
            callback_data="back_to_categories",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="cancel",
        )
    )

    return builder.as_markup()
