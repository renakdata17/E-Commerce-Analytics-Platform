"""Seed Acme Outfitters reference SKUs + WEST-DC availability."""

from __future__ import annotations

import pathlib
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

LIBS = pathlib.Path(__file__).resolve().parents[3] / "libs"

sys.path.insert(0, str(LIBS))

from ecommerce_platform.settings import settings  # noqa: E402
from ecommerce_platform.db.models import InventoryItem, Product, Warehouse  # noqa: E402

CATALOG: list[tuple[str, str, int]] = [
    ("SKU-WOOL-CAR-COAT", "Nordic Carry Car Coat — Graphite Heather", 18_995),
    ("SKU-SOLE-RUN-V3", "Crestline Runner V3 — Ember Red", 12_495),
    ("SKU-CHINO-SLUB", "Mercantile Slub Stretch Chino", 8950),
    ("SKU-STORM-SHELL-LT", "Trellis Waterproof Shell Lite", 9995),
]


def seed_inventory() -> None:
    engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with SessionLocal() as session:
        west = session.scalar(select(Warehouse).where(Warehouse.code == "WEST-DC"))
        if west is None:
            west = Warehouse(code="WEST-DC", region="AMER-Pacific")
            session.add(west)
            session.flush()

        for sku, title, cents in CATALOG:
            product = session.scalar(select(Product).where(Product.sku == sku))
            if product is None:
                product = Product(sku=sku, title=title, currency="USD", unit_price_cents=cents)
                session.add(product)
                session.flush()

            inventory = session.scalar(
                select(InventoryItem).where(
                    InventoryItem.product_id == product.id,
                    InventoryItem.warehouse_id == west.id,
                )
            )

            if inventory is None:
                reorder = max(120, cents // 200)
                inventory = InventoryItem(
                    product_id=product.id,
                    warehouse_id=west.id,
                    qty_on_hand=475,
                    qty_reserved=0,
                    reorder_point=reorder,
                )
                session.add(inventory)

        session.commit()


def main() -> None:
    seed_inventory()


if __name__ == "__main__":
    main()
