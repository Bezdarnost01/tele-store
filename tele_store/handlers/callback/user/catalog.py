from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import F, Router

from tele_store.crud.category import CategoryManager
from tele_store.crud.product import ProductManager
from tele_store.keyboards.inline.product_order_menu import product_order_keyboard
from tele_store.keyboards.inline.user_category_menu import get_user_category_keyboard
from tele_store.keyboards.inline.user_product_menu import get_user_product_keyboard

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "catalog")
async def open_catalog(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать пользователю список категорий."""
    keyboard, total = await get_user_category_keyboard(session=session)

    if total == 0:
        await call.answer("Категории пока не добавлены.", show_alert=True)
        return

    await call.answer()
    await call.message.answer("📂 Выберите категорию:", reply_markup=keyboard)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(call: CallbackQuery, session: AsyncSession) -> None:
    """Вернуться к списку категорий."""
    keyboard, total = await get_user_category_keyboard(session=session)

    if total == 0:
        await call.answer("Категории пока недоступны.", show_alert=True)
        return

    await call.answer()

    try:
        await call.message.edit_reply_markup()
    except Exception:
        logger.debug("Не удалось очистить клавиатуру сообщения", exc_info=True)

    await call.message.answer("📂 Выберите категорию:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("user_category_page:"))
async def paginate_categories(call: CallbackQuery, session: AsyncSession) -> None:
    """Переключение страниц списка категорий."""
    page = int(call.data.split(":")[1])
    keyboard, total = await get_user_category_keyboard(session=session, page=page)

    if total == 0:
        await call.answer("Категории пока отсутствуют.", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("user_category:"))
async def open_category(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать товары выбранной категории."""
    _, category_id_raw, *_ = call.data.split(":")
    category_id = int(category_id_raw)

    category = await CategoryManager.get_category(
        session=session, category_id=category_id
    )

    if category is None:
        await call.answer("Категория не найдена.", show_alert=True)
        return

    keyboard, total = await get_user_product_keyboard(
        session=session, category_id=category_id
    )

    if total == 0:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    await call.answer()
    await call.message.answer(
        f"🛍 <b>{category.name}</b>\nВыберите товар для оформления заказа:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("user_product_page:"))
async def paginate_products(call: CallbackQuery, session: AsyncSession) -> None:
    """Переключение страниц товаров внутри категории."""
    _, category_raw, page_raw = call.data.split(":")
    category_id = int(category_raw)
    page = int(page_raw)

    keyboard, total = await get_user_product_keyboard(
        session=session, category_id=category_id, page=page
    )

    if total == 0:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("user_product:"))
async def show_product_preview(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать карточку товара с предложением оформить заказ."""
    _, product_raw, category_raw, page_raw = call.data.split(":")
    product_id = int(product_raw)
    category_id = int(category_raw)
    page = int(page_raw)

    product = await ProductManager.get_product(session=session, product_id=product_id)

    if product is None or not product.is_active:
        await call.answer("Товар недоступен.", show_alert=True)
        return

    caption = (
        f"📦 <b>{product.name}</b>\n"
        f"💵 Цена: {product.price} ₽\n"
        f"📜 Описание: {product.description or '—'}"
    )

    keyboard = product_order_keyboard(
        category_id=category_id, product_id=product.id, page=page
    )

    if product.photo_file_id:
        await call.message.answer_photo(
            product.photo_file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    else:
        await call.message.answer(caption, reply_markup=keyboard)

    await call.answer()
