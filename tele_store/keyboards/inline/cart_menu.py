from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tele_store.models.models import Cart


def build_cart_keyboard(cart: Cart) -> InlineKeyboardMarkup:
    """Собрать клавиатуру управления корзиной."""

    builder = InlineKeyboardBuilder()

    for item in cart.items:
        product_name = (
            item.product.name if item.product is not None else f"ID {item.product_id}"
        )
        builder.row(
            InlineKeyboardButton(
                text="➖",
                callback_data=f"cart_decrease:{item.id}",
            ),
            InlineKeyboardButton(
                text=f"{item.quantity}",
                callback_data=f"cart_ignore:{item.id}",
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart_increase:{item.id}",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 Удалить {product_name[:20]}",
                callback_data=f"cart_remove:{item.id}",
            )
        )

    if cart.items:
        builder.row(
            InlineKeyboardButton(
                text="🧾 Оформить заказ",
                callback_data="checkout_cart",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🧹 Очистить корзину",
                callback_data="cart_clear",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к категориям",
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
