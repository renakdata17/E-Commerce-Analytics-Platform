"""Environment-driven configuration reused by FastAPI deployments."""

from __future__ import annotations

import tomllib
from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _guess_repo_root() -> Path:
    """`libs/ecommerce_platform/settings.py` → repository root."""

    here = Path(__file__).resolve()
    return here.parents[2]


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    DATABASE_URL_SYNC: str = Field(
        default="postgresql+psycopg://analytics:analytics@localhost:5432/ecommerce",
    )

    DATABASE_URL_ASYNC: str = Field(
        default="postgresql+psycopg_async://analytics:analytics@localhost:5432/ecommerce",
    )

    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    KAFKA_BOOTSTRAP: str = Field(default="localhost:9092")

    DISABLE_KAFKA: bool = Field(default=False)

    JWT_SECRET: str = Field(default="CHANGE_ME_IN_REAL_ENVIRONMENT")
    JWT_ISSUER: str = Field(default="acme-auth")
    JWT_ALG: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    ADMIN_BOOTSTRAP_EMAIL: str | None = Field(default="ops.lead@acme-outfitters.demo")
    ADMIN_BOOTSTRAP_PASSWORD: str | None = Field(default="ChangeMeBootstrap!")

    MOCK_PAYMENT_APPROVAL: bool = Field(
        default=True,
        description="When true checkout auto-marks PAID for demo corridors.",
    )

    @cached_property
    def repo_root(self) -> Path:
        return _guess_repo_root()


def runtime_version() -> str:
    root = _guess_repo_root()
    manifest = root / "pyproject.toml"
    if not manifest.exists():
        return "0.0.dev0"
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    return str(data.get("project", {}).get("version", "0.0.dev0"))


settings = ServiceSettings()
