from aiogram import Router

from tele_store.handlers.callback import admin_callbacks, callbacks, user_callbacks
from tele_store.handlers.command import admin_command_router, start_command_router
from tele_store.handlers.message import admin_message, user_message


def setup_routers() -> Router:
    """Создать и настроить основной роутер."""
    router = Router()

    routers = [
        start_command_router.router,
        admin_command_router.router,
        admin_callbacks.router,
        user_callbacks.router,
        callbacks.router,
        admin_message.router,
        user_message.router,
    ]

    for r in routers:
        router.include_router(r)

    return router
