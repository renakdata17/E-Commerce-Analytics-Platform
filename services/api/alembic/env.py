"""Alembic environment for operational DDL."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

LIBS = Path(__file__).resolve().parents[3] / "libs"

_LIB_PATH = str(LIBS)
if _LIB_PATH not in sys.path:
    sys.path.insert(0, _LIB_PATH)

from ecommerce_platform.db import models as _registration  # noqa: F401
from ecommerce_platform.db.base import Base
from ecommerce_platform.settings import settings

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run DDL without live transaction context."""

    context.configure(url=settings.DATABASE_URL_SYNC, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Interactive migration path hooked by Alembic CLI."""

    connectable = engine_from_config(
        {"sqlalchemy.url": settings.DATABASE_URL_SYNC},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
