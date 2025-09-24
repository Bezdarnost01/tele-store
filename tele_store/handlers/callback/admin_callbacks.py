import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.crud.product import ProductManager
from tele_store.filters.admin_filter import IsAdmin
from tele_store.keyboards.inline.cancel_button import cancel_key
from tele_store.keyboards.inline.item_list_menu import get_item_list_menu_keyboard
from tele_store.keyboards.inline.item_preview_menu import item_preview_key
from tele_store.keyboards.inline.order_list_menu import get_order_list_menu_keyboard
from tele_store.schemas.product import CreateProduct
from tele_store.states.states import AddNewItem

router = Router()
logger = logging.getLogger(__name__)


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
async def remove_item_handler(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер для отображения списка товаров"""
    await call.answer()

    keyboard = await get_item_list_menu_keyboard(session=session)
    await call.message.answer("📦 Список товаров:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("page:"))
async def paginate_items(call: CallbackQuery, session: AsyncSession) -> None:
    """Хендлер переключения страниц"""
    page = int(call.data.split(":")[1])
    keyboard = await get_item_list_menu_keyboard(session=session, page=page)

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("item_preview:"))
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


@router.callback_query(F.data.startswith("remove_item:"))
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
