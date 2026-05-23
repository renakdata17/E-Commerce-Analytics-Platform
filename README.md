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

## Local development

See `infra/README.md` for Compose services (Kafka, PostgreSQL, Redis, MinIO) and bootstrap notes.

### Service quickstarts

- **API:** `cd services/api && pip install -r requirements.txt && uvicorn app.main:app --reload`
- **Workers:** Redis broker URL must match Compose (documented in `services/workers/README.md`)

## Roles (ownership)

**Data Engineer:** Kafka schemas & producers, Flink jobs, dbt models, Airflow DAGs, GE suites, lake ingestion to S3/MinIO.

**Backend Developer:** FastAPI REST/WebSocket, GraphQL against PostgreSQL, Celery tasks, auth service, Docker Compose + K8s for dev and deployment.

---

This repository is a structured baseline; extend each subsystem with domain-specific schemas and workloads.
