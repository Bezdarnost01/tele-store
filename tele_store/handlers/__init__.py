from aiogram import Router

from tele_store.handlers.command import start_command_router


def setup_routers() -> Router:
    """Создать и настроить основной роутер."""
    router = Router()
    router.include_routers(start_command_router.router)
    return router
