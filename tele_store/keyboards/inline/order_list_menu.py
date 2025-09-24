from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tele_store.config.config_reader import config
from tele_store.crud.order import OrderManager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_order_list_menu_keyboard(
    session: AsyncSession, page: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    item_list = await OrderManager.list_orders(session=session)

    start = (page - 1) * config.ORDERS_PER_PAGE
    end = start + config.ORDERS_PER_PAGE
    page_items = item_list[start:end]

    for item in page_items:
        builder.row(
            InlineKeyboardButton(
                text=f"{item.name} — {item.price} ₽",
                callback_data=f"item_preview:{item.id}",
            )
        )

    total_pages = (
        len(item_list) + config.ORDERS_PER_PAGE - 1
    ) // config.ORDERS_PER_PAGE
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
