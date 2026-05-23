"""Operational OLTP entities for orders, catalogue, warehouses, inventory."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecommerce_platform.enums import OrderStatus
from ecommerce_platform.db.base import Base


def _uuid_pk() -> str:
    return str(uuid.uuid4())


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False)

    inventory_rows: Mapped[list["InventoryItem"]] = relationship(back_populates="warehouse")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    inventory_rows: Mapped[list["InventoryItem"]] = relationship(back_populates="product")


class InventoryItem(Base):
    """Per-warehouse SKU availability used for pessimistic concurrency on checkout."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_wh"),
        CheckConstraint("qty_on_hand >= 0", name="ck_inventory_qty_non_negative"),
        CheckConstraint("qty_reserved >= 0", name="ck_reserved_non_negative"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    warehouse_id: Mapped[str] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    qty_on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    product: Mapped[Product] = relationship(back_populates="inventory_rows")
    warehouse: Mapped[Warehouse] = relationship(back_populates="inventory_rows")


class CustomerAccount(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)


class MerchantUser(Base):
    """Internal dashboards / tooling users separate from storefront customers."""

    __tablename__ = "merchant_users"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_analyst: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", native_enum=False, length=32),
        nullable=False,
        insert_default=OrderStatus.PENDING_PAYMENT,
        server_default=OrderStatus.PENDING_PAYMENT.value,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    lines: Mapped[list["OrderLine"]] = relationship(cascade="all, delete-orphan", back_populates="order")


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=_uuid_pk)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_snapshot_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship(back_populates="lines")
