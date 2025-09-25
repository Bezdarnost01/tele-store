from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tele_store.config.config_reader import config
from tele_store.crud.category import CategoryManager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_category_list_menu_keyboard(
    session: AsyncSession, page: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    category_list = await CategoryManager.list_categories(session=session)

    start = (page - 1) * config.CATEGORIES_PER_PAGE
    end = start + config.CATEGORIES_PER_PAGE
    page_categorys = category_list[start:end]

    for category in page_categorys:
        builder.row(
            InlineKeyboardButton(
                text=f"{category.name}",
                callback_data=f"category_preview:{category.id}",
            )
        )

    total_pages = (
        len(category_list) + config.CATEGORIES_PER_PAGE - 1
    ) // config.CATEGORIES_PER_PAGE
    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад", callback_data=f"category_page:{page - 1}"
            )
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️", callback_data=f"category_page:{page + 1}"
            )
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
