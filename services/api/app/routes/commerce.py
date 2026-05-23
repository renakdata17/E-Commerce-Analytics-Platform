"""Public commerce + telemetry APIs."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Annotated

import redis.asyncio as redis_py
from ecommerce_platform.enums import AnalyticsChannel
from ecommerce_platform.events_schema import KafkaEnvelope, PageViewEvent
from ecommerce_platform.kafka_topics import CLICKS
from ecommerce_platform.schemas.http import CheckoutRequest, CheckoutResponse, ClickBatchRequest
from ecommerce_platform.settings import settings
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import (
    get_async_session,
    redis_client_factory,
    schedule_order_receipt_stub,
    schedule_restock_alert_stub,
)
from app.services.checkout import InsufficientInventory, finalize_checkout

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout_cart(
    request: Request,
    payload: CheckoutRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis_client: Annotated[redis_py.Redis, Depends(redis_client_factory)],
):
    kafka_bus = request.app.state.kafka_bus
    try:
        order = await finalize_checkout(
            session=session,
            redis_client=redis_client,
            event_bus_emitter=kafka_bus,
            notifier=schedule_order_receipt_stub,
            reorder_notifier=schedule_restock_alert_stub,
            payload=payload,
            mock_payment=settings.MOCK_PAYMENT_APPROVAL,
        )
    except InsufficientInventory as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CheckoutResponse(
        order_id=str(order.id),
        status=order.status.value,
        total_cents=order.total_cents,
    )


@router.post("/events/clicks/batch")
async def ingest_click_batch(request: Request, batch: ClickBatchRequest) -> dict:
    bus = request.app.state.kafka_bus
    import datetime as dt

    emitted = 0
    errors: list[str] = []
    for evt in batch.events:
        try:
            if bus.enabled:
                payload = PageViewEvent(
                    envelope=KafkaEnvelope(emitted_at=dt.datetime.now(dt.UTC)),
                    visitor_id=evt.visitor_id,
                    sku=evt.sku,
                    referrer=evt.referrer,
                    session_id=evt.session_id,
                    millis_on_page_hint=evt.millis_on_page_hint,
                )
                await bus.emit_json(
                    CLICKS,
                    key=evt.visitor_id,
                    value={
                        **payload.model_dump(mode="json"),
                        "channel_hint": AnalyticsChannel.WEB_APP.value,
                    },
                )
            emitted += 1
        except Exception:
            LOGGER.exception("failed click ingest for visitor=%s", evt.visitor_id)
            errors.append(str(exc))

    return {
        "accepted": emitted,
        "failures": errors,
        "kafka_attached": bus.enabled,
    }


@router.websocket("/ws/live-metrics")
async def live_dashboard_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    redis_client = redis_py.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("dashboard:signals")
    ping_task = asyncio.create_task(_websocket_keepalive(websocket))
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
    except WebSocketDisconnect:
        LOGGER.debug("dashboard subscriber disconnected")
    finally:
        ping_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ping_task

        await pubsub.unsubscribe("dashboard:signals")
        await pubsub.aclose()
        await redis_client.aclose()


async def _websocket_keepalive(ws: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(20)
            await ws.send_json({"kind": "keepalive"})
    except Exception:
        return

