"""Application dependency wiring."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator

import redis.asyncio as redis_py
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ecommerce_platform.auth.jwt import JWTPayload, decode_token
from ecommerce_platform.settings import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

LOGGER = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

_ENGINE: AsyncEngine | None = None
_SESSION_FACTORY: async_sessionmaker[AsyncSession] | None = None


def _bootstrap_engine_locked() -> None:
    global _ENGINE, _SESSION_FACTORY
    if _SESSION_FACTORY:
        return
    _ENGINE = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False, pool_pre_ping=True)
    _SESSION_FACTORY = async_sessionmaker(_ENGINE, autoflush=False, expire_on_commit=False)


async def shutdown_database() -> None:
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None:
        return
    await _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    _bootstrap_engine_locked()
    assert _SESSION_FACTORY is not None

    async with _SESSION_FACTORY() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def redis_client_factory() -> AsyncGenerator[redis_py.Redis, None]:
    client = redis_py.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def jwt_principal_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> JWTPayload | None:
    if creds is None:
        return None

    token = creds.credentials
    try:
        return decode_token(
            token,
            secret=settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            issuer=settings.JWT_ISSUER,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token") from exc


async def require_analyst(
    principal: JWTPayload | None = Depends(jwt_principal_optional),
) -> JWTPayload:
    if principal is None or not principal.analyst:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Requires analyst entitlement")
    return principal


def schedule_order_receipt_stub(summary: dict[str, object]) -> None:
    try:
        if os.getenv("PYTEST_RUNNING") == "1":
            return

        from merchant_workers.tasks import send_order_receipt_stub

        send_order_receipt_stub.delay(summary)
    except Exception as exc:  # pragma: no cover - dev without celery module path
        LOGGER.debug("receipt enqueue skipped (%s)", exc)


def schedule_restock_alert_stub(sku: str, qty_hand: int, reorder_point: int) -> None:
    try:
        if os.getenv("PYTEST_RUNNING") == "1":
            return

        from merchant_workers.tasks import maybe_escalate_restock

        maybe_escalate_restock.delay(sku, qty_hand, reorder_point)
    except Exception as exc:  # pragma: no cover
        LOGGER.debug("restock enqueue skipped (%s)", exc)