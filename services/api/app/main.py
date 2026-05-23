"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse


app = FastAPI(
    title="E-Commerce Analytics API",
    description="REST + GraphQL façade over operational Postgres and realtime feeds.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
