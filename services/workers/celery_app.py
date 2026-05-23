"""Celery application factory — wire broker URL from environment in production."""

import os

from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

app = Celery("ecommerce_workers", broker=BROKER, backend=BROKER)


@app.task(name="workers.ping")
def ping() -> str:
    return "pong"
