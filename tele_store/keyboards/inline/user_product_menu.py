from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tele_store.config.config_reader import config
from tele_store.crud.product import ProductManager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_product_keyboard(
    session: AsyncSession,
    *,
    category_id: int,
    page: int = 1,
) -> tuple[InlineKeyboardMarkup, int]:
    """Сформировать клавиатуру с товарами выбранной категории."""
    builder = InlineKeyboardBuilder()

    products = await ProductManager.list_products(
        session=session, category_id=category_id
    )

    start = (page - 1) * config.ITEMS_PER_PAGE
    end = start + config.ITEMS_PER_PAGE
    page_products = products[start:end]

    for product in page_products:
        builder.row(
            InlineKeyboardButton(
                text=f"{product.name} — {product.price} ₽",
                callback_data=f"user_product:{product.id}:{category_id}:{page}",
            )
        )

    total_pages = (len(products) + config.ITEMS_PER_PAGE - 1) // config.ITEMS_PER_PAGE
    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"user_product_page:{category_id}:{page - 1}",
            )
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=f"user_product_page:{category_id}:{page + 1}",
            )
        )

    if pagination_buttons:
        builder.row(*pagination_buttons)

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

    return builder.as_markup(), len(products)
