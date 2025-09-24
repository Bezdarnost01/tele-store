from pydantic import BaseModel


class CreateUser(BaseModel):
    user_id: int
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class UserUpdate(BaseModel):
    name: str | None
    phone: str | None
    address: str | None
