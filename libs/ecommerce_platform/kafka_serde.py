"""JSON helpers for deterministic Kafka payloads."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID


def kafka_json_dumps(data: dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), cls=_KafkaEncoder).encode("utf-8")


class _KafkaEncoder(json.JSONEncoder):
    def default(self, o: Any):  # type: ignore[override]
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)
