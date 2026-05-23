## Acme Outfitters commerce API

The FastAPI façade combines transactional REST endpoints, Strawberry GraphQL, Redis-backed WebSockets, Celery callbacks, and **optional Kafka** emits (automatically degraded when `DISABLE_KAFKA=true` or when `aiokafka` wheels are unavailable—common on bleeding-edge Python builds).

Everything imports domain logic from `libs/ecommerce_platform/`, which must precede `services/api` on `PYTHONPATH`.

### Install + run Uvicorn (PowerShell)

```powershell
cd services/api
python -m pip install -r requirements.txt          # excludes aiokafka by default

# OPTIONAL: Kafka async producer (preferred on Python 3.11–3.12/Linux CI)
python -m pip install -r ../../extras/kafka-async.txt

$RepoRoot = (Resolve-Path "..\\..").Path
$Env:PYTHONPATH = "$RepoRoot\\libs;$RepoRoot\\services\\api;$RepoRoot\\services\\workers;$Env:PYTHONPATH"

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Flip `DISABLE_KAFKA=false` plus install `extras/kafka-async.txt` whenever you want the API to hydrate `events.*` topics from local Compose Kafka.

### Database bootstrap (PostgreSQL via Compose defaults)

Assuming `infra/docker-compose.yml` Postgres is reachable as `postgresql://analytics:analytics@localhost:5432/ecommerce`:

```powershell
cd services/api
$Env:PYTHONPATH = "..\\..\\libs;$Env:PYTHONPATH"

python -m alembic -c alembic.ini upgrade head
python scripts/seed_catalog.py
```

Override `DATABASE_URL_SYNC` / `DATABASE_URL_ASYNC` if you tunnel to RDS or Cloud SQL—the async URL should use `postgresql+psycopg_async://...`.
