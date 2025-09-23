from decimal import Decimal

from pydantic import BaseModel

from tele_store.db.enums import OrderStatus


class CreateOrder(BaseModel):
    order_number: str
    user_id: int | None = None
    total_price: Decimal = Decimal(0)
    delivery_method: str | None = None
    status: OrderStatus = OrderStatus.NEW

class UpdateOrder(BaseModel):
    order_number: str | None = None
    user_id: int | None = None
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
