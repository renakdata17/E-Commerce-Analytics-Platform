# E-Commerce Analytics Platform

End-to-end reference architecture for event-driven commerce analytics: ingestion → streaming → batch → quality → APIs → consumers.

## Architecture

| Layer | Responsibility |
|--------|----------------|
| **Ingestion** | Click & session events, orders, checkout, inventory, 3rd-party (shipping, CRM) |
| **Streaming** | Apache Kafka topics (`events.clicks`, `events.orders`, `events.inventory`, `events.shipping`) |
| **Processing** | Flink (real-time aggregation), dbt (batch transforms), Airflow (orchestration), Great Expectations (quality) |
| **Storage** | PostgreSQL (operational), Snowflake/DuckDB (analytics), Redis (cache/live counters), S3/MinIO (raw lake Parquet) |
| **API** | FastAPI (REST + WebSocket), GraphQL layer, Celery workers, JWT/OAuth2 auth service |
| **Web / App** | Dashboards (Grafana / Metabase), internal tools, mobile clients |

## Repository layout

```
infra/                 Docker Compose + Kubernetes manifests
services/api/          FastAPI + GraphQL (Strawberry) entrypoint
services/auth/         JWT / OAuth2 service
services/workers/      Celery background jobs
pipelines/producers/   Kafka producer clients
pipelines/flink-jobs/  Stream processing jobs
pipelines/dbt/         Transformation models (staging → marts)
pipelines/airflow/dags Batch DAGs
data-quality/expectations/  Great Expectations suites
tests/                 Unit + integration tests
```

## Demo storyline: Acme Outfitters

The repo ships an opinionated-but-runnable exemplar retailer:

| Flow | Behaviour |
|------|-----------|
| **Catalogue ingestion** | `services/api/scripts/seed_catalog.py` creates `WEST-DC` stocking four hero SKUs (wool car coat, running shoe, chino shell, ultralite shell). |
| **Checkout** | `POST /api/v1/checkout` pessimistically locks `inventory_items`, decrements availability, mocks payment → `events.orders`/`events.inventory`, bumps Redis rollup hashes, emits Celery receipt + reorder hooks. |
| **Click telemetry** | `POST /api/v1/events/clicks/batch` mirrors storefront sessions into `events.clicks` (+ channel hint metadata). |
| **Live dashboards** | `GET /api/v1/ws/live-metrics` consumes Redis `dashboard:signals` broadcasts written during checkout alongside keep-alive pings for stale proxies. |
| **Analytics contracts** | `GET /graphql` exposes catalogue + fulfilment-hub hints for analysts tooling (GraphiQL bundled). JWT-gated endpoints live under `/api/v1/analyst`. |

Supporting services:

- **`services/auth`**: Issues OAuth2 password tokens validated by the commerce API (`python-jose`, shared `JWT_SECRET`).
- **`services/workers`**: Implements receipt + escalation Celery stubs (`merchant_workers.tasks`).

Kafka note: installs default to pure-Python stacks so Windows/Python 3.14 agents pass CI—install `extras/kafka-async.txt` when you compile `aiokafka` successfully.

## Local development

See `infra/README.md` for Compose services (Kafka, PostgreSQL, Redis, MinIO) and bootstrap notes.

### Developer quickstarts

- **Operational API:** Follow `services/api/README.md` (PYTHONPATH/Kafka nuances).
- **Auth service:** `cd services/auth && pip install -r requirements.txt`, set `JWT_SECRET`, then `python -m uvicorn app.main:app --reload --port 8010`.
- **Workers:** Ensure `CELERY_BROKER_URL` matches Compose Redis and `PYTHONPATH` includes repo `libs/` + `services/workers/` for `merchant_workers.tasks`.

## Roles (ownership)

**Data Engineer:** Kafka schemas & producers, Flink jobs, dbt models, Airflow DAGs, GE suites, lake ingestion to S3/MinIO.

**Backend Developer:** FastAPI REST/WebSocket, GraphQL against PostgreSQL, Celery tasks, auth service, Docker Compose + K8s for dev and deployment.

---

This codebase is deliberately dense: it stitches operational commerce with streaming contracts, Celery choreography, Redis fan-out, Snowflake-ready dbt models, and scaffolding for Flink/GX/Airflow. Extend each subsystem—especially dbt sources + GE suites—with your upstream lake tables rather than rewriting the façade.
