"""Create initial database schema"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202501070001"
down_revision = None
branch_labels = None
depends_on = None


order_status_enum = sa.Enum(
    "new", "processing", "shipped", "delivered", "canceled", name="order_status"
)


def upgrade() -> None:
    order_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("photo_file_id", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("price >= 0", name="price_non_negative"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_products_category_id", "products", ["category_id"], unique=False
    )
    op.create_index("ix_products_name", "products", ["name"], unique=False)

    op.create_table(
        "carts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_carts_user_id", "carts", ["user_id"], unique=True)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
        sa.UniqueConstraint(
            "cart_id", "product_id", name="uq_cartitem_cart_product"
        ),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"], unique=False)
    op.create_index(
        "ix_cart_items_product_id", "cart_items", ["product_id"], unique=False
    )
    op.create_index(
        "ix_cart_items_cart_product",
        "cart_items",
        ["cart_id", "product_id"],
        unique=False,
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "total_price",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("delivery_method", sa.String(length=64), nullable=True),
        sa.Column("status", order_status_enum, nullable=False, server_default="new"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("total_price >= 0", name="total_price_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_orders_order_number", "orders", ["order_number"], unique=True
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="orderitem_qty_positive"),
        sa.CheckConstraint("price >= 0", name="orderitem_price_non_negative"),
        sa.UniqueConstraint(
            "order_id", "product_id", name="uq_orderitem_order_product"
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_order_items_order_id", "order_items", ["order_id"], unique=False
    )
    op.create_index(
        "ix_order_items_product_id", "order_items", ["product_id"], unique=False
    )
    op.create_index(
        "ix_order_items_order_product",
        "order_items",
        ["order_id", "product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_items_order_product", table_name="order_items")
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_cart_items_cart_product", table_name="cart_items")
    op.drop_index("ix_cart_items_product_id", table_name="cart_items")
    op.drop_index("ix_cart_items_cart_id", table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index("ix_carts_user_id", table_name="carts")
    op.drop_table("carts")

    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_table("products")

    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")

    op.drop_table("users")

    order_status_enum.drop(op.get_bind(), checkfirst=True)
