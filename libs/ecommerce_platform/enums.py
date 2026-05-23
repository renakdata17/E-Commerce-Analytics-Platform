from __future__ import annotations

from enum import StrEnum


class OrderStatus(StrEnum):
    DRAFT = "draft"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    FULFILLING = "fulfilling"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class InventoryMovement(StrEnum):
    RECEIPT = "receipt"
    SALE = "sale"
    RESTOCK_ALERT = "restock_alert"


class AnalyticsChannel(StrEnum):
    WEB_APP = "web_app"
    MOBILE = "mobile"
    STORE_POS = "store_pos"

