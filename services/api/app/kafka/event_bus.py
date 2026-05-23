"""Async Kafka producer wrapper — aiokafka is optional when compiler wheels unavailable."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ecommerce_platform.kafka_serde import kafka_json_dumps
from ecommerce_platform.settings import settings

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover
    from aiokafka import AIOKafkaProducer  # type: ignore[import-not-found]
    from aiokafka.errors import KafkaError  # type: ignore[import-not-found]

    _HAVE_AIOKAFKA = True
except ImportError:  # pragma: no cover
    KafkaError = Exception  # type: ignore[assignment,misc]

    class AIOKafkaProducer:  # type: ignore[too-many-lines]
        def __init__(self, *_a, **_k) -> None:  # noqa: D401
            raise RuntimeError("Install aiokafka (see extras/kafka-async.txt) to enable Kafka")

    _HAVE_AIOKAFKA = False


class EventBus:
    """Kafka façade that degrades when DISABLE_KAFKA is true or aiokafka isn't installed."""

    def __init__(self, enabled: bool = True) -> None:
        self._requested = enabled
        self._enabled = enabled and _HAVE_AIOKAFKA
        if self._requested and not _HAVE_AIOKAFKA:
            LOGGER.warning(
                "Kafka emits disabled (aiokafka missing). Operational API remains functional."
            )
        self._producer: AIOKafkaProducer | None = None  # type: ignore[valid-type]
        self._lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def start(self) -> None:
        if not self._enabled:
            return
        async with self._lock:
            if self._producer is None:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP,
                    compression_type="gzip",
                )
                await self._producer.start()

    async def shutdown(self) -> None:
        if self._producer is None:
            return
        async with self._lock:
            await self._producer.stop()
            self._producer = None

    async def emit_json(self, topic: str, key: str | None, value: dict[str, Any]) -> None:
        if not self._enabled or self._producer is None:
            LOGGER.debug("kafka noop topic=%s", topic)
            return
        try:
            await self._producer.send_and_wait(
                topic,
                kafka_json_dumps(value),
                key=key.encode("utf-8") if key else None,
            )
        except KafkaError as exc:  # pragma: no cover
            LOGGER.warning("kafka emit failed topic=%s err=%s", topic, exc)
