import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.crud.product import ProductManager
from tele_store.keyboards.inline.catalog_list_menu import get_catalog_list_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "test")
async def open_catalog(call: CallbackQuery, session: AsyncSession) -> None: 
    """Открыть каталог товаров"""
    await call.answer()
    await call.message.answer()