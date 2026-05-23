"""Versioned payloads that flow through Kafka."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, PositiveInt


class KafkaEnvelope(BaseModel):
    schema_version: Annotated[int, Field(ge=1)] = 1
    emitted_at: datetime


class PageViewEvent(BaseModel):
    envelope: KafkaEnvelope
    visitor_id: str
    sku: str
    referrer: str | None = None
    session_id: str
    millis_on_page_hint: Annotated[int, Field(ge=0)]


class Money(BaseModel):
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "USD"
    cents: int


class OrderLineSnapshot(BaseModel):
    sku: str
    qty: PositiveInt
    unit_price: Money


class OrderPlacedEvent(BaseModel):
    envelope: KafkaEnvelope
    order_id: str
    customer_email: str
    lines: list[OrderLineSnapshot]
    totals: Money
    fulfillment_warehouse_codes: list[str]


class InventoryChangedEvent(BaseModel):
    envelope: KafkaEnvelope
    sku: str
    warehouse_code: str
    delta_qty: int
    reason: str
    qty_on_hand_after: Annotated[int, Field(ge=0)]


class CarrierDispatchStub(BaseModel):
    envelope: KafkaEnvelope
    order_id: str
    carrier: str
    tracking_number: str
    shipped_at: datetime
