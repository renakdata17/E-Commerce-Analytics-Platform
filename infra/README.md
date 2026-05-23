## Local infrastructure

Kafka (with ZooKeeper), PostgreSQL, Redis, and MinIO — aligned with ingestion, operational store, caching, and a raw lake stand-in.

### Start

From this directory:

```bash
docker compose up -d
```

### Default endpoints

| Service    | Connection |
|-----------|-------------|
| Kafka     | `localhost:9092` |
| PostgreSQL | `postgresql://analytics:analytics@localhost:5432/ecommerce` |
| Redis     | `redis://localhost:6379` |
| MinIO S3 API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |

### Topics (recommended)

Provision in your Kafka tooling or a small bootstrap script:

- `events.clicks`
- `events.orders`
- `events.inventory`
- `events.shipping`
