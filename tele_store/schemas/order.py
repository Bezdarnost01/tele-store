from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from tele_store.db.enums import OrderStatus


class CreateOrder(BaseModel):
    order_number: str
    tg_id: int | None = None
    name: str
    phone: str
    address: str
    total_price: Decimal = Decimal(0)
    delivery_method: str | None = None
    status: OrderStatus = OrderStatus.NEW


class UpdateOrder(BaseModel):
    order_number: str | None = None
    tg_id: int | None = None
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    total_price: Decimal | None = None
    delivery_method: str | None = None
    status: OrderStatus | None = None


class CreateOrderItem(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    price: Decimal


class UpdateOrderItem(BaseModel):
    quantity: int | None = None
    price: Decimal | None = None
