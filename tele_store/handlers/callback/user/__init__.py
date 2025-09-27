from aiogram import Router

from . import cart, catalog, checkout

router = Router()

for sub_router in (catalog.router, cart.router, checkout.router):
    router.include_router(sub_router)

__all__ = ["router"]
