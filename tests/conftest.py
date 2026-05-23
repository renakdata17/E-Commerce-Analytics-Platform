"""Pytest bootstrapping — must run before `app.main` resolves settings singletons."""

from __future__ import annotations

import os

os.environ.setdefault("DISABLE_KAFKA", "true")
os.environ.setdefault("PYTEST_RUNNING", "1")
os.environ.setdefault(
    "DATABASE_URL_ASYNC",
    "postgresql+psycopg_async://analytics:analytics@localhost:5432/ecommerce",
)
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql+psycopg://analytics:analytics@localhost:5432/ecommerce")
