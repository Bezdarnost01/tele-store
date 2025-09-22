import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from filters.admin_filter import IsAdmin

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(message: Message, command: CommandObject) -> None:
    user_name = message.from_user.first_name
    await message.answer(f"Привет, {user_name}")


@router.message(IsAdmin(), Command("admin"))
async def admin_command(message: Message, command: CommandObject) -> None:
    admin_name = message.from_user.first_name
    await message.answer(f"Привет, {admin_name}")
