from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import F, Router

from tele_store.crud.cart import CartManager
from tele_store.crud.order import OrderManager
from tele_store.handlers.callback.user.shared import (
    build_order_preview_text,
    collect_cart_lines,
    format_money,
    generate_order_number,
    refresh_cart_view,
    sanitize_cart,
)
from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.order_confirm_menu import order_confirm_keyboard
from tele_store.schemas.order import CreateOrder, CreateOrderItem
from tele_store.states.states import NewDelivery

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "checkout_cart")
async def start_checkout(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Запустить процесс оформления заказа из корзины."""
    cart = await CartManager.get_cart_by_user(session=session, tg_id=call.from_user.id)
    if cart is None or not cart.items:
        await call.answer(
            "Корзина пуста. Добавьте товары перед оформлением.", show_alert=True
        )
        await refresh_cart_view(call, session)
        return

    cleaned_cart = await sanitize_cart(session, cart) or cart
    if cleaned_cart is None or not cleaned_cart.items:
        await call.answer(
            "В корзине не осталось доступных товаров. Добавьте новые позиции.",
            show_alert=True,
        )
        await refresh_cart_view(call, session)
        return

    await state.clear()
    await state.set_state(NewDelivery.name)
    await state.update_data(cart_id=cleaned_cart.id)

    await call.answer()
    try:
        await call.message.edit_text(
            "Отличный выбор! Давай оформим заказ. Как к тебе обращаться?",
            reply_markup=cancel_key(),
        )
    except Exception:
        logger.debug(
            "Не удалось обновить сообщение корзины перед оформлением", exc_info=True
        )
        await call.message.answer(
            "Отличный выбор! Давай оформим заказ. Как к тебе обращаться?",
            reply_markup=cancel_key(),
        )


@router.callback_query(
    NewDelivery.delivery_method, F.data.in_(["select_courier", "select_self-delivery"])
)
async def choose_delivery_method(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Получить желаемый способ доставки перед подтверждением заказа."""
    delivery_method = "Курьер" if call.data == "select_courier" else "Самовывоз"

    await state.update_data(delivery_method=delivery_method)
    await state.set_state(NewDelivery.confirm)

    data = await state.get_data()
    cart_id = data.get("cart_id")

    if cart_id is None:
        await state.clear()
        await call.message.answer(
            "❌ Корзина не найдена. Попробуйте начать оформление заново.",
            reply_markup=cancel_key(),
        )
        await call.answer(show_alert=True)
        return

    cart = await CartManager.get_cart(session=session, cart_id=int(cart_id))
    cart = await sanitize_cart(session, cart) if cart else cart

    if cart is None or not cart.items:
        await state.clear()
        await call.message.answer(
            "❌ Корзина пуста. Добавьте товары и начните оформление заново.",
        )
        await call.answer(show_alert=True)
        return

    preview = build_order_preview_text(cart, data)
    await call.answer()
    await call.message.answer(preview, reply_markup=order_confirm_keyboard())


@router.callback_query(NewDelivery.confirm, F.data == "confirm_order")
async def confirm_order(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Подтвердить заказ из корзины и сохранить его в базе."""
    data = await state.get_data()
    cart_id = data.get("cart_id")

    if cart_id is None:
        await state.clear()
        await call.message.edit_text(
            "❌ Не удалось найти корзину. Попробуйте оформить заказ заново."
        )
        await call.answer(show_alert=True)
        return

    cart = await CartManager.get_cart(session=session, cart_id=int(cart_id))
    cart = await sanitize_cart(session, cart) if cart else cart

    if cart is None or not cart.items:
        await state.clear()
        await call.message.edit_text(
            "❌ Корзина пуста. Добавьте товары и попробуйте снова."
        )
        await call.answer(show_alert=True)
        return

    lines, total_price = collect_cart_lines(cart)
    if not lines:
        await state.clear()
        await call.message.edit_text(
            "❌ В корзине нет доступных товаров. Попробуйте добавить новые позиции."
        )
        await call.answer(show_alert=True)
        return

    order_number = generate_order_number()
    order_payload = CreateOrder(
        order_number=order_number,
        tg_id=call.from_user.id,
        name=data.get("name"),
        phone=data.get("phone_number"),
        address=data.get("address"),
        total_price=total_price,
        delivery_method=data.get("delivery_method"),
    )

    order = await OrderManager.create_order(session=session, payload=order_payload)

    for item in cart.items:
        product = item.product
        if product is None:
            continue
        await OrderManager.create_order_item(
            session=session,
            payload=CreateOrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price,
            ),
        )

    await CartManager.clear_cart(session=session, cart_id=cart.id)

    items_text = "\n".join(lines)
    summary = (
        "✅ <b>Заказ оформлен!</b>\n\n"
        f"Номер заказа: <code>{order_number}</code>\n"
        f"{items_text}\n\n"
        f"Итого: <b>{format_money(total_price)}</b>\n\n"
        f"Имя: {data.get('name')}\n"
        f"Телефон: {data.get('phone_number')}\n"
        f"Адрес: {data.get('address')}\n"
        f"Доставка: {data.get('delivery_method')}\n\n"
        "Мы свяжемся с вами в ближайшее время для уточнения деталей."
    )

    await call.message.edit_text(summary)
    await state.clear()
    await call.answer("Заказ успешно создан!", show_alert=True)
