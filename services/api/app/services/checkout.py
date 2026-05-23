"""Core commerce checkout with inventory locking."""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from collections.abc import Callable
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_platform.enums import InventoryMovement, OrderStatus
from ecommerce_platform.events_schema import (
    InventoryChangedEvent,
    KafkaEnvelope,
    Money,
    OrderLineSnapshot,
    OrderPlacedEvent,
)
from ecommerce_platform.kafka_topics import INVENTORY as INVENTORY_TOPIC, ORDERS
from ecommerce_platform.db.models import InventoryItem, Order, OrderLine, Product, Warehouse
from ecommerce_platform.schemas.http import CheckoutRequest

PRIMARY_WAREHOUSE_CODE = "WEST-DC"


class InsufficientInventory(Exception):
    def __init__(self, sku: str, demanded: int, available: int) -> None:
        msg = f"SKU {sku} unavailable (need {demanded}, have {available})"
        super().__init__(msg)
        self.sku = sku


async def finalize_checkout(
    *,
    session: AsyncSession,
    redis_client: Redis,
    event_bus_emitter,
    notifier: Callable[[dict[str, Any]], None],
    reorder_notifier: Callable[[str, int, int], None],
    payload: CheckoutRequest,
    mock_payment: bool,
) -> Order:
    """Validate demand, pessimistically decrement primary DC stock, persist order."""

    sku_demand: Counter[str] = Counter({line.sku: line.qty for line in payload.lines})

    sku_lookup: dict[str, Product] = {}
    for sku in sku_demand:
        product = await session.scalar(select(Product).where(Product.sku == sku))
        if product is None:
            msg = f"Unknown SKU {sku}"
            raise ValueError(msg)
        sku_lookup[sku] = product

    warehouse = await session.scalar(select(Warehouse).where(Warehouse.code == PRIMARY_WAREHOUSE_CODE))
    if warehouse is None:
        raise RuntimeError("Primary warehouse seed missing")

    inventory_moves: list[InventoryChangedEvent] = []
    restock_candidates: list[tuple[str, int, int]] = []

    for sku, needed in sku_demand.items():
        product = sku_lookup[sku]
        stmt = (
            select(InventoryItem)
            .where(
                InventoryItem.product_id == product.id,
                InventoryItem.warehouse_id == warehouse.id,
            )
            .with_for_update(of=InventoryItem)
        )
        row = await session.scalar(stmt)
        if row is None or row.qty_on_hand < needed:
            raise InsufficientInventory(sku, needed, getattr(row, "qty_on_hand", 0))

        row.qty_on_hand -= needed
        inventory_moves.append(
            InventoryChangedEvent(
                envelope=_kafka_envelope(),
                sku=sku,
                warehouse_code=PRIMARY_WAREHOUSE_CODE,
                delta_qty=-needed,
                reason=InventoryMovement.SALE.value,
                qty_on_hand_after=row.qty_on_hand,
            )
        )
        restock_candidates.append((sku, row.qty_on_hand, row.reorder_point))

    total_cents = 0
    order_lines_entities: list[OrderLine] = []
    kafka_line_snapshots: list[OrderLineSnapshot] = []
    currency = payload.currency.upper()

    for line in payload.lines:
        product = sku_lookup[line.sku]
        line_total = product.unit_price_cents * line.qty
        total_cents += line_total
        order_lines_entities.append(
            OrderLine(
                product_id=product.id,
                qty=line.qty,
                unit_price_snapshot_cents=product.unit_price_cents,
            )
        )
        kafka_line_snapshots.append(
            OrderLineSnapshot(
                sku=line.sku,
                qty=line.qty,
                unit_price=Money(currency=currency, cents=product.unit_price_cents),
            )
        )

    payment_state = OrderStatus.PAID if mock_payment else OrderStatus.PENDING_PAYMENT
    order = Order(
        email=str(payload.email),
        currency=currency,
        total_cents=total_cents,
        status=payment_state,
        lines=order_lines_entities,
    )
    session.add(order)
    await session.flush()
    await session.refresh(order)

    if payment_state is OrderStatus.PAID:
        order_event = OrderPlacedEvent(
            envelope=_kafka_envelope(),
            order_id=str(order.id),
            customer_email=str(payload.email),
            lines=kafka_line_snapshots,
            totals=Money(currency=currency, cents=total_cents),
            fulfillment_warehouse_codes=[PRIMARY_WAREHOUSE_CODE],
        )
        await event_bus_emitter.emit_json(
            ORDERS,
            str(order.id),
            order_event.model_dump(mode="json"),
        )

        for change in inventory_moves:
            await event_bus_emitter.emit_json(
                INVENTORY_TOPIC,
                change.sku,
                change.model_dump(mode="json"),
            )

        await _publish_dashboard(redis_client, total_cents, str(order.id))
        notifier(
            {
                "order_id": str(order.id),
                "customer_email": str(payload.email),
                "currency": currency,
                "total_cents": total_cents,
            }
        )
        for sku, qty_hand, reorder_point in restock_candidates:
            if qty_hand <= reorder_point:
                reorder_notifier(sku, qty_hand, reorder_point)

    return order


def _kafka_envelope() -> KafkaEnvelope:
    return KafkaEnvelope(emitted_at=dt.datetime.now(tz=dt.UTC))


async def _publish_dashboard(redis_client: Redis, gross_cents: int, order_id: str) -> None:
    payload = {"type": "order_paid", "order_id": order_id, "gross_cents": gross_cents}
    await redis_client.hincrby("metrics:rollup", "orders_paid_total", 1)
    await redis_client.hincrby("metrics:rollup", "gmv_usd_cents", gross_cents)
    await redis_client.publish("dashboard:signals", json.dumps(payload))