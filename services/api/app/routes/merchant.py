"""Analyst-facing read surfaces."""

from __future__ import annotations

from typing import Any

from ecommerce_platform.auth.jwt import JWTPayload
from ecommerce_platform.db.models import Order, OrderLine, Product
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_async_session, require_analyst

router = APIRouter(prefix="/api/v1/analyst", tags=["merchant"])


@router.get("/orders/{order_id}")
async def read_order_projection(
    order_id: str,
    analyst: JWTPayload = Depends(require_analyst),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    _ = analyst

    order = await session.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="order not found")

    rows = await session.execute(
        select(OrderLine, Product.sku.label("sku"))
        .join(Product, OrderLine.product_id == Product.id)
        .where(OrderLine.order_id == order.id)
    )

    line_payload = []
    for line, sku in rows.all():
        line_payload.append(
            {
                "sku": sku,
                "qty": line.qty,
                "price_snapshot_cents": line.unit_price_snapshot_cents,
            }
        )

    return {
        "order_id": str(order.id),
        "placed_at": order.placed_at.isoformat(),
        "email": order.email,
        "status": getattr(order.status, "value", str(order.status)),
        "currency": order.currency,
        "total_cents": order.total_cents,
        "lines": line_payload,
    }
