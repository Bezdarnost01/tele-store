import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from tele_store.crud.user import UserManager
from tele_store.keyboards.inline.user_menu import user_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()

    tg_id = message.from_user.id
    user_name = message.from_user.first_name
    user = await UserManager.get_user(session=session, tg_id=tg_id)

    if not user:
        await UserManager.create_user(session=session, tg_id=tg_id)

    await message.answer(
        f"Привет, {user_name}!\n\n Готов сделать заказ?",
        reply_markup=user_menu_keyboard(),
    )
