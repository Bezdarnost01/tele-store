from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tele_store.db.enums import OrderStatus

STATUS_TITLES: dict[OrderStatus, str] = {
    OrderStatus.NEW: "🆕 Новый",
    OrderStatus.PROCESSING: "⚙️ В обработке",
    OrderStatus.SHIPPED: "🚚 Отправлен",
    OrderStatus.DELIVERED: "📦 Доставлен",
    OrderStatus.CANCELED: "❌ Отменён",
}


def order_status_keyboard(
    *, order_id: int, current_status: OrderStatus
) -> InlineKeyboardMarkup:
    """Собрать клавиатуру для смены статуса заказа (статусы по 2 в ряд)."""
    builder = InlineKeyboardBuilder()

    for status, title in STATUS_TITLES.items():
        if status == current_status:
            button_text = f"✅ {title}"
            callback_data = f"order_status_ignore:{order_id}"
        else:
            button_text = title
            callback_data = f"order_status:{order_id}:{status.value}"

        builder.button(text=button_text, callback_data=callback_data)

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(
            text="⬅️ К списку заказов",
            callback_data="orders_list",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить заказ",
            callback_data=f"delete_order:{order_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="cancel",
        )
    )

    return builder.as_markup()
