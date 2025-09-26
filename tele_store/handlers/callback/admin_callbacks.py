import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.crud.category import CategoryManager
from tele_store.crud.order import OrderManager
from tele_store.crud.product import ProductManager
from tele_store.filters.admin_filter import IsAdmin
from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.categories_list_menu import (
    get_category_list_menu_keyboard,
)
from tele_store.keyboards.inline.category_preview_menu import category_preview_key
from tele_store.keyboards.inline.item_list_menu import get_item_list_menu_keyboard
from tele_store.keyboards.inline.item_preview_menu import item_preview_key
from tele_store.keyboards.inline.order_list_menu import get_order_list_menu_keyboard
from tele_store.keyboards.inline.order_status_menu import (
    STATUS_TITLES,
    order_status_keyboard,
)
from tele_store.db.enums import OrderStatus
from tele_store.schemas.order import UpdateOrder
from tele_store.schemas.product import CreateProduct
from tele_store.states.states import AddNewCategory, AddNewItem

if TYPE_CHECKING:
    from tele_store.models.models import Order

router = Router()
logger = logging.getLogger(__name__)


MONEY_STEP = Decimal("0.01")


def format_money(amount: Decimal) -> str:
    """Отформатировать денежную сумму для сообщений."""

    return f"{amount.quantize(MONEY_STEP)} ₽"


def build_order_preview_text(order: Order) -> str:
    """Подготовить текст с подробной информацией о заказе."""

    status_title = STATUS_TITLES.get(order.status, str(order.status))
    customer = order.user.tg_id if getattr(order, "user", None) else order.tg_id
    customer_text = str(customer) if customer is not None else "Не указан"
    delivery_text = order.delivery_method or "Не указана"

    lines: list[str] = []
    for index, item in enumerate(order.items, start=1):
        product_name = (
            item.product.name if getattr(item, "product", None) else f"ID {item.product_id}"
        )
        line_total = item.price * item.quantity
        lines.append(
            f"{index}. {product_name} — {item.quantity} шт. × "
            f"{format_money(item.price)} = {format_money(line_total)}"
        )

    if not lines:
        lines.append("— товары отсутствуют —")

    items_block = "\n".join(lines)

    return (
        f"📦 <b>Заказ {order.order_number}</b>\n"
        f"ID: {order.id}\n"
        f"Статус: {status_title}\n"
        f"Покупатель: {customer_text}\n"
        f"Сумма: {format_money(order.total_price)}\n"
        f"Доставка: {delivery_text}\n\n"
        f"Состав заказа:\n{items_block}"
    )



@router.callback_query(IsAdmin(), F.data == "add_new_item")
async def add_new_item_handler(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Хендлер для добавления нового товара"""
    await state.clear()
    await state.set_state(AddNewItem.name)

    await call.answer()
    await call.message.answer(
        "Введите наименование товара: ", reply_markup=cancel_key()
    )


@router.callback_query(IsAdmin(), F.data == "item_list")
async def get_item_list_handler(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер для отображения списка товаров"""
    await call.answer()

    keyboard = await get_item_list_menu_keyboard(session=session)
    await call.message.answer("📦 Список товаров:", reply_markup=keyboard)


@router.callback_query(IsAdmin(), F.data.startswith("item_page:"))
async def paginate_items(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер переключения страниц айтемов"""
    page = int(call.data.split(":")[1])
    keyboard = await get_item_list_menu_keyboard(session=session, page=page)

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(IsAdmin(), F.data.startswith("item_preview:"))
async def item_selected(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер предросмотра товара"""
    item_id = int(call.data.split(":")[1])
    product = await ProductManager.get_product(session=session, product_id=item_id)

    if not product:
        await call.answer("❌ Товар не найден", show_alert=True)
        return

    caption = (
        f"📦 <b>{product.name}</b>\n"
        f"ℹ Айди: <code>{product.id}</code>\n"
        f"💵 Цена: {product.price} ₽\n"
        f"📜 Описание: {product.description or '—'}"
    )

    if product.photo_file_id:
        await call.message.answer_photo(
            photo=product.photo_file_id,
            caption=caption,
            reply_markup=item_preview_key(item_id=product.id),
        )
    else:
        await call.message.answer(
            caption, reply_markup=item_preview_key(item_id=product.id)
        )

    await call.answer()


@router.callback_query(IsAdmin(), F.data.startswith("remove_item:"))
async def item_selected(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер предросмотра товара"""
    item_id = int(call.data.split(":")[1])
    product = await ProductManager.get_product(session=session, product_id=item_id)

    if not product:
        await call.answer("❌ Товар не найден", show_alert=True)
        return

    await ProductManager.delete_product(session=session, product_id=item_id)

    await call.answer(f"✅ Товар {product.name} успешно удален!", show_alert=True)
    await call.message.delete()


@router.callback_query(IsAdmin(), F.data == "orders_list")
async def orders_list_handler(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер для просмотра списка заказов"""
    await call.answer()

    keyboard = await get_order_list_menu_keyboard(session=session)
    await call.message.answer("📄 Список заказов", reply_markup=keyboard)


@router.callback_query(IsAdmin(), F.data.startswith("orders_page:"))
async def paginate_orders(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер переключения страниц списка заказов."""

    page = int(call.data.split(":")[1])
    keyboard = await get_order_list_menu_keyboard(session=session, page=page)

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(IsAdmin(), F.data.startswith("order_preview:"))
async def show_order_preview(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер детального просмотра заказа."""

    order_id = int(call.data.split(":")[1])
    order = await OrderManager.get_order(session=session, order_id=order_id)

    if order is None:
        await call.answer("❌ Заказ не найден", show_alert=True)
        return

    text = build_order_preview_text(order)
    keyboard = order_status_keyboard(
        order_id=order.id, current_status=order.status
    )

    await call.answer()
    await call.message.answer(text, reply_markup=keyboard)


@router.callback_query(IsAdmin(), F.data.startswith("order_status:"))
async def change_order_status(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер изменения статуса заказа."""

    _, order_raw, status_raw = call.data.split(":")
    order_id = int(order_raw)

    try:
        new_status = OrderStatus(status_raw)
    except ValueError:
        await call.answer("❌ Неизвестный статус", show_alert=True)
        return

    updated = await OrderManager.update_order(
        session=session,
        order_id=order_id,
        payload=UpdateOrder(status=new_status),
    )

    if updated is None:
        await call.answer("❌ Заказ не найден", show_alert=True)
        return

    order = await OrderManager.get_order(session=session, order_id=order_id)
    if order is None:
        order = updated

    text = build_order_preview_text(order)
    keyboard = order_status_keyboard(
        order_id=order_id, current_status=order.status
    )

    try:
        await call.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        logger.debug("Не удалось обновить сообщение заказа", exc_info=True)

    status_title = STATUS_TITLES.get(new_status, new_status.value)
    if order.tg_id:
        try:
            await call.bot.send_message(
                order.tg_id,
                (
                    f"ℹ️ Статус вашего заказа {order.order_number} обновлён:\n"
                    f"<b>{status_title}</b>"
                ),
            )
        except Exception:
            logger.warning(
                "Не удалось отправить уведомление пользователю %s",
                order.tg_id,
                exc_info=True,
            )

    await call.answer("Статус заказа обновлён.")


@router.callback_query(IsAdmin(), F.data.startswith("order_status_ignore:"))
async def ignore_order_status(call: CallbackQuery) -> None:
    """Хендлер для уже установленного статуса заказа."""

    await call.answer("Этот статус уже установлен.")


@router.callback_query(IsAdmin(), AddNewItem.confirm, F.data == "add_new_item_confirm")
async def add_new_item_confirm_handler(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Хендлер для подтверждения добавления товара"""
    data = await state.get_data()

    new_item = CreateProduct(
        category_id=int(data["category_id"]),
        name=data["name"],
        description=data["description"],
        price=Decimal(data["price"]),
        photo_file_id=data["photo_file_id"],
        is_active=True,
    )

    await ProductManager.create_product(session=session, payload=new_item)

    await call.answer("✅ Товар успешно добавлен!", show_alert=True)
    await state.clear()
    await call.message.delete()


@router.callback_query(IsAdmin(), AddNewItem.confirm, F.data == "add_new_item_cancel")
async def add_new_item_cancel_handler(call: CallbackQuery, state: FSMContext) -> None:
    """Хендлер для отмены добавления товара"""
    await call.answer("❌ Добавление товара отменено.", show_alert=True)
    await state.clear()
    await call.message.delete()


@router.callback_query(IsAdmin(), F.data == "add_new_category")
async def add_new_category_handler(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Хендлер для добавления нового товара"""
    await state.clear()
    await state.set_state(AddNewCategory.name)

    await call.answer()
    await call.message.answer(
        "Введите наименование категории: ", reply_markup=cancel_key()
    )


@router.callback_query(
    IsAdmin(), AddNewCategory.confirm, F.data == "add_new_category_cancel"
)
async def add_new_category_cancel_handler(
    call: CallbackQuery, state: FSMContext
) -> None:
    """Хендлер для отмены добавления категории"""
    await call.answer("❌ Добавление категории отменено.", show_alert=True)
    await state.clear()
    await call.message.delete()


@router.callback_query(IsAdmin(), F.data == "categories_list")
async def category_list_handler(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер для отображения списка категорий"""
    await call.answer()

    keyboard = await get_category_list_menu_keyboard(session=session)
    await call.message.answer("📜 Список категорий:", reply_markup=keyboard)


@router.callback_query(IsAdmin(), F.data.startswith("category_page:"))
async def paginate_category(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер переключения страниц категорий"""
    page = int(call.data.split(":")[1])
    keyboard = await get_category_list_menu_keyboard(session=session, page=page)

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(IsAdmin(), F.data.startswith("category_preview:"))
async def category_selected(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер предросмотра категории"""
    category_id = int(call.data.split(":")[1])
    category = await CategoryManager.get_category(
        session=session, category_id=category_id
    )

    if not category:
        await call.answer("❌ Категория не найдена", show_alert=True)
        return

    caption = (
        f"📦 <b>{category.name}</b>\n"
        f"ℹ Айди: <code>{category.id}</code>\n"
        f"📜 Описание: {category.description or '—'}"
    )

    await call.message.answer(
        caption, reply_markup=category_preview_key(category_id=category.id)
    )

    await call.answer()


@router.callback_query(
    IsAdmin(), AddNewCategory.confirm, F.data == "add_new_category_confirm"
)
async def add_new_category_confirm_handler(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Хендлер для подтверждения добавления категории"""
    data = await state.get_data()

    await CategoryManager.create_category(
        session=session, name=data["name"], description=data["description"]
    )

    await call.answer("✅ Категория успешно добавлена!", show_alert=True)
    await state.clear()
    await call.message.delete()


@router.callback_query(
    IsAdmin(), AddNewCategory.confirm, F.data == "add_new_category_cancel"
)
async def add_new_category_cancel_handler(
    call: CallbackQuery, state: FSMContext
) -> None:
    """Хендлер для отмены добавления категории"""
    await call.answer("❌ Добавление категории отменено.", show_alert=True)
    await state.clear()
    await call.message.delete()


@router.callback_query(IsAdmin(), F.data.startswith("remove_category:"))
async def category_selected(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер для удаления категории"""
    category_id = int(call.data.split(":")[1])
    category = await CategoryManager.get_category(
        session=session, category_id=category_id
    )

    if not category:
        await call.answer("❌ Категория не найдена", show_alert=True)
        return

    await CategoryManager.delete_category(session=session, category_id=category_id)

    await call.answer(f"✅ Категория {category.name} успешно удалена!", show_alert=True)
    await call.message.delete()
