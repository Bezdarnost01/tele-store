from aiogram import Router


def setup_routers() -> Router:
    from .command import start_command_router

    router = Router()
    router.include_routers(start_command_router.router)

    return router
