from pydantic import BaseModel


class AddCartItem(BaseModel):
    cart_id: int
    product_id: int
    quantity: int = 1


class UpdateCartItemCount(BaseModel):
    cart_item_id: int
    quantity: int
