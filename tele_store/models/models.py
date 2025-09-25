from __future__ import annotations

from datetime import datetime  # noqa: TC003
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tele_store.db.db import Base
from tele_store.db.enums import OrderStatus

if TYPE_CHECKING:
    from decimal import Decimal

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )

    cart: Mapped[Cart] = relationship(back_populates="user", uselist=False)
    orders: Mapped[list[Order]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя для отладки."""
        return f"<User id={self.id} tg_id={self.tg_id!r}>"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    products: Mapped[list[Product]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Строковое представление категории."""
        return f"<Category id={self.id} name={self.name!r}>"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    photo_file_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    category: Mapped[Category] = relationship(back_populates="products")
    cart_items: Mapped[list[CartItem]] = relationship(
        back_populates="product", cascade="all, delete", passive_deletes=True
    )
    order_items: Mapped[list[OrderItem]] = relationship(back_populates="product")

    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    def __repr__(self) -> str:
        """Строковое представление товара."""
        return f"<Product id={self.id} name={self.name!r} price={self.price}>"


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id", ondelete="CASCADE"), unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="cart")
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        """Строковое представление корзины."""
        return f"<Cart id={self.id} tg_id={self.tg_id}>"


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cart: Mapped[Cart] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="cart_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        UniqueConstraint("cart_id", "product_id", name="uq_cartitem_cart_product"),
        Index("ix_cart_items_cart_product", "cart_id", "product_id"),
    )

    def __repr__(self) -> str:
        """Строковое представление позиции корзины."""
        return (
            f"<CartItem cart_id={self.cart_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    tg_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id", ondelete="SET NULL"), nullable=True, index=True
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    delivery_method: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="order_status"),
        default=OrderStatus.NEW,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint("total_price >= 0", name="total_price_non_negative"),
    )

    def __repr__(self) -> str:
        """Строковое представление заказа."""
        return (
            f"<Order id={self.id} tg_id={self.tg_id} "
            f"status={self.status} total={self.total_price}>"
        )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="orderitem_qty_positive"),
        CheckConstraint("price >= 0", name="orderitem_price_non_negative"),
        UniqueConstraint("order_id", "product_id", name="uq_orderitem_order_product"),
        Index("ix_order_items_order_product", "order_id", "product_id"),
    )

    def __repr__(self) -> str:
        """Строковое представление позиции заказа."""
        return (
            f"<OrderItem order_id={self.order_id} "
            f"product_id={self.product_id} qty={self.quantity} price={self.price}>"
        )
