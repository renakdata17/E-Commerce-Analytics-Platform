"""Synchronous Postgres access for MerchantUser lookup + bootstrap."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ecommerce_platform.settings import settings

engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
