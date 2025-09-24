import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tele_store.filters.admin_filter import IsAdmin
from tele_store.keyboards.inline.admin_menu import admin_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(IsAdmin(), Command("admin"))
async def admin_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    admin_name = message.from_user.first_name
    await message.answer(
        f"Привет, {admin_name}!\n\n Добро пожаловать в админ панель.",
        reply_markup=admin_menu_keyboard(),
    )
