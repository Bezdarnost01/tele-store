import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.config_reader import config
from handlers import setup_routers
from models import init_all_databases


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
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.exception("Unhandled exception: %s", e)
