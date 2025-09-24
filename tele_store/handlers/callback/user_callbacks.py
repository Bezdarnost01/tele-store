import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "test")
async def buy_card(call: CallbackQuery, session: AsyncSession) -> None: ...
