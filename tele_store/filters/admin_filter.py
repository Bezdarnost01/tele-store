from aiogram.filters import BaseFilter
from aiogram.types import Message

from tele_store.config.config_reader import config


class IsAdmin(BaseFilter):
    """Проверяет, является ли пользователь администратором."""

    async def __call__(self, message: Message) -> bool:
        """Вернуть ``True``, если отправитель сообщения в списке админов."""
        return message.from_user.id in config.ADMINS
