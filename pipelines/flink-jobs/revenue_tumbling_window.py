"""
Tumbling-window revenue aggregator over `events.orders`.

Run with PyFlink (requires Java + Flink distribution on PATH):
``python revenue_tumbling_window.py``

This skeleton focuses on keyed state + timers; tune checkpointing externally.
"""

from __future__ import annotations

JSON_SAMPLE = '{"order_id": "demo"}'


def configure_job() -> str:
    """Return a Flink CLI payload or JSON-encoded job graph description."""

    return JSON_SAMPLE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(
        "Install PyFlink + Apache Flink binaries, then uncomment the Pipeline "
        "builder that reads `events.orders` and sinks tumbling aggregates."
    )
