from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tele_store.config.config_reader import config
from tele_store.crud.product import ProductManager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_catalog_list_menu_keyboard(
    session: AsyncSession, category_id: int, page: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    product_list = await ProductManager.list_products(
        session=session, category_id=category_id
    )

    start = (page - 1) * config.PRODUCTS_PER_PAGE
    end = start + config.PRODUCTS_PER_PAGE
    page_products = product_list[start:end]

    for product in page_products:
        builder.row(
            InlineKeyboardButton(
                text=f"{product.name} — {product.price} ₽",
                callback_data=f"product_preview:{product.id}",
            )
        )

    total_pages = (
        len(product_list) + config.PRODUCTS_PER_PAGE - 1
    ) // config.PRODUCTS_PER_PAGE
    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{page - 1}")
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"page:{page + 1}")
        )

    if pagination_buttons:
        builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text="❌ Скрыть",
            callback_data="cancel",
        )
    )

    return builder.as_markup()
