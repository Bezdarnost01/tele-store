from decimal import Decimal

from pydantic import BaseModel


class CreateProduct(BaseModel):
    category_id: int
    name: str
    price: Decimal
    description: str | None = None
    photo_file_id: str | None = None
    is_active: bool = True

class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    photo_file_id: str | None = None
    is_active: bool | None = None
