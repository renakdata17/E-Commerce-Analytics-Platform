"""Celery application wired to Postgres + Redis-backed broker."""

from __future__ import annotations

import logging
import os

from celery import Celery

LOGGER = logging.getLogger(__name__)

BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

app = Celery(
    "ecommerce_workers",
    broker=BROKER,
    backend=BROKER,
)

app.conf.imports = ("merchant_workers.tasks",)


@app.task(name="workers.ping")
def ping() -> str:
    return "pong"
