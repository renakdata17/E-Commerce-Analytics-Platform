"""Strawberry GraphQL façade for exploratory analyst queries."""

from __future__ import annotations

from dataclasses import dataclass

import strawberry
from ecommerce_platform.db.models import Product
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class GraphQLRequestContext:
    session: AsyncSession


@strawberry.type(name="Warehouse")
class WarehouseGQL:
    code: str
    region: str


@strawberry.type(name="CatalogueSKU")
class ProductGQL:
    sku: str
    title: str
    price_cents: int
    fulfilment_hub_code: str | None


@strawberry.type(name="Queries")
class Query:
    @strawberry.field(description="Operational catalogue slice used by storefront + analysts.")
    async def catalogue(self, info: strawberry.Info) -> list[ProductGQL]:
        ctx: GraphQLRequestContext = info.context["ctx"]
        result = await ctx.session.scalars(select(Product))

        hint = info.context.get("default_dc_code")
        rows: list[ProductGQL] = []
        for product in result:
            rows.append(
                ProductGQL(
                    sku=product.sku,
                    title=product.title,
                    price_cents=product.unit_price_cents,
                    fulfilment_hub_code=str(hint) if hint else None,
                )
            )
        return rows

    @strawberry.field
    async def warehouse_directory(self, info: strawberry.Info) -> list[WarehouseGQL]:
        ctx: GraphQLRequestContext = info.context["ctx"]
        from ecommerce_platform.db.models import Warehouse

        result = await ctx.session.scalars(select(Warehouse))
        return [WarehouseGQL(code=w.code, region=w.region) for w in result]


schema = strawberry.Schema(query=Query)
