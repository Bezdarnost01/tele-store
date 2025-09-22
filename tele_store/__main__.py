import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tele_store.config.config_reader import config
from tele_store.handlers import setup_routers
from tele_store.models import init_all_databases

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(
        token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await init_all_databases()

    dp = Dispatcher()
    dp.include_router(setup_routers())

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception:
        logger.exception("Unhandled exception")
