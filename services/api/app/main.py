"""FastAPI application wiring REST, GraphQL, WebSocket feeds, Kafka, and Postgres."""

from __future__ import annotations

from contextlib import asynccontextmanager

from ecommerce_platform.settings import runtime_version, settings
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.deps import get_async_session, shutdown_database
from app.graphql.schema import GraphQLRequestContext, schema as gql_schema
from app.kafka.event_bus import EventBus
from app.routes import commerce, merchant


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = EventBus(enabled=not settings.DISABLE_KAFKA)
    app.state.kafka_bus = bus
    await bus.start()
    try:
        yield
    finally:
        await bus.shutdown()
        await shutdown_database()


async def gql_context_dependency(
    session: AsyncSession = Depends(get_async_session),
):
    from app.services import checkout as checkout_service

    return {
        "ctx": GraphQLRequestContext(session=session),
        "default_dc_code": checkout_service.PRIMARY_WAREHOUSE_CODE,
    }


def build_app() -> FastAPI:
    app = FastAPI(
        title="Acme Outfitters Commerce API",
        description="Operational APIs with analytics-friendly contracts.",
        version=runtime_version(),
        lifespan=lifespan,
    )

    graphql_router = GraphQLRouter(
        schema=gql_schema,
        graphql_ide="graphiql",
        context_getter=gql_context_dependency,
    )

    app.include_router(commerce.router, tags=["commerce"])
    app.include_router(merchant.router)
    app.include_router(graphql_router, prefix="/graphql")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "api-ok"}

    return app


app = build_app()
