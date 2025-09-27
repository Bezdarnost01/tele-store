from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest

from tele_store.crud.cart import CartManager
from tele_store.crud.product import ProductManager
from tele_store.handlers.callback.user.shared import (
    build_cart_text,
    refresh_cart_view,
    sanitize_cart,
)
from tele_store.keyboards.inline.cart_menu import build_cart_keyboard
from tele_store.schemas.cart import AddCartItem, UpdateCartItemCount

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "cart")
async def open_cart(call: CallbackQuery, session: AsyncSession) -> None:
    """Показать пользователю содержимое корзины."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    cleaned_cart = await sanitize_cart(session, cart) if cart else cart

    if cleaned_cart is None or not cleaned_cart.items:
        await call.answer("Сейчас корзина пуста.", show_alert=True)
        return

    if cleaned_cart is not cart:
        await call.answer(
            "Некоторые товары больше недоступны и были убраны из корзины.",
            show_alert=True,
        )
    else:
        await call.answer()

    text = build_cart_text(cleaned_cart)
    keyboard = build_cart_keyboard(cleaned_cart)
    await call.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cancel_order")
async def cancel_order(call: CallbackQuery, state: FSMContext) -> None:
    """Отменить оформление заказа и очистить состояние."""
    if await state.get_state() is not None:
        await state.clear()
    try:
        await call.message.edit_text(
            "❌ Оформление заказа отменено. Корзина сохранена, можно продолжить покупки."
        )
    except TelegramBadRequest:
        logger.debug("Не удалось обновить сообщение при отмене заказа", exc_info=True)
    await call.answer()


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_product_to_cart(call: CallbackQuery, session: AsyncSession) -> None:
    """Добавить выбранный товар в корзину пользователя."""
    product_id = int(call.data.split(":")[1])
    product = await ProductManager.get_product(session=session, product_id=product_id)

    if product is None or not product.is_active:
        await call.answer("Товар недоступен для добавления.", show_alert=True)
        return

    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None:
        cart = await CartManager.create_cart(session=session, tg_id=call.from_user.id)

    existing_item = await CartManager.get_cart_item_by_product(
        session=session, cart_id=cart.id, product_id=product.id
    )

    if existing_item is None:
        await CartManager.add_cart_item(
            session=session,
            payload=AddCartItem(cart_id=cart.id, product_id=product.id, quantity=1),
        )
    else:
        await CartManager.update_cart_item_count(
            session=session,
            payload=UpdateCartItemCount(
                cart_item_id=existing_item.id,
                quantity=existing_item.quantity + 1,
            ),
        )

    await call.answer("Добавлено в корзину!")


@router.callback_query(F.data.startswith("cart_increase:"))
async def increase_cart_item(call: CallbackQuery, session: AsyncSession) -> None:
    """Увеличить количество товара в корзине."""
    item_id = int(call.data.split(":")[1])
    cart_item = await CartManager.get_cart_item(session=session, cart_item_id=item_id)

    if cart_item is None or cart_item.cart.tg_id != call.from_user.id:
        await call.answer("Товар не найден в корзине.", show_alert=True)
        return

    await CartManager.update_cart_item_count(
        session=session,
        payload=UpdateCartItemCount(
            cart_item_id=cart_item.id,
            quantity=cart_item.quantity + 1,
        ),
    )

    await refresh_cart_view(call, session)
    await call.answer("Количество увеличено.")


@router.callback_query(F.data.startswith("cart_decrease:"))
async def decrease_cart_item(call: CallbackQuery, session: AsyncSession) -> None:
    """Уменьшить количество товара в корзине."""
    item_id = int(call.data.split(":")[1])
    cart_item = await CartManager.get_cart_item(session=session, cart_item_id=item_id)

    if cart_item is None or cart_item.cart.tg_id != call.from_user.id:
        await call.answer("Товар не найден в корзине.", show_alert=True)
        return

    new_quantity = cart_item.quantity - 1
    if new_quantity <= 0:
        await CartManager.delete_cart_item(session=session, cart_item_id=cart_item.id)
        await refresh_cart_view(call, session)
        await call.answer("Товар удалён из корзины.")
        return

    await CartManager.update_cart_item_count(
        session=session,
        payload=UpdateCartItemCount(
            cart_item_id=cart_item.id,
            quantity=new_quantity,
        ),
    )

    await refresh_cart_view(call, session)
    await call.answer("Количество уменьшено.")


@router.callback_query(F.data.startswith("cart_remove:"))
async def remove_cart_item(call: CallbackQuery, session: AsyncSession) -> None:
    """Удалить выбранный товар из корзины."""
    item_id = int(call.data.split(":")[1])
    cart_item = await CartManager.get_cart_item(session=session, cart_item_id=item_id)

    if cart_item is None or cart_item.cart.tg_id != call.from_user.id:
        await call.answer("Товар уже отсутствует в корзине.", show_alert=True)
        return

    await CartManager.delete_cart_item(session=session, cart_item_id=cart_item.id)
    await refresh_cart_view(call, session)
    await call.answer("Товар удалён.")


@router.callback_query(F.data == "cart_clear")
async def clear_cart(call: CallbackQuery, session: AsyncSession) -> None:
    """Полностью очистить корзину пользователя."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None or not cart.items:
        await call.answer("Корзина уже пуста.", show_alert=True)
        return

    await CartManager.clear_cart(session=session, cart_id=cart.id)
    await refresh_cart_view(call, session)
    await call.answer("Корзина очищена.")


@router.callback_query(F.data.startswith("cart_ignore:"))
async def ignore_cart_info(call: CallbackQuery) -> None:
    """Обработать нажатие на неактивную кнопку количества."""
    await call.answer()
