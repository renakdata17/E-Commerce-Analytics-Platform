"""Central registry for Kafka topics used across producers, Flink, and dbt ingestion."""

CLICKS = "events.clicks"
ORDERS = "events.orders"
INVENTORY = "events.inventory"
SHIPPING = "events.shipping"

ALL_TOPICS: tuple[str, ...] = (CLICKS, ORDERS, INVENTORY, SHIPPING)
