"""Stub producer for ecommerce events."""
import json
import logging
from datetime import UTC, datetime
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOOTSTRAP = "localhost:9092"


def make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def publish_example(topic: str = "events.clicks") -> None:
    producer = make_producer()
    payload = {
        "event_id": "stub-001",
        "occurred_at": datetime.now(tz=UTC).isoformat(),
        "sku": "DEMO-SKU",
    }
    future = producer.send(topic, key=payload["event_id"], value=payload)
    future.add_errback(lambda exc: logger.error("kafka send failed: %s", exc))
    producer.flush(timeout=10)
    logger.info("Published to %s: %s", topic, payload)


if __name__ == "__main__":
    publish_example()
