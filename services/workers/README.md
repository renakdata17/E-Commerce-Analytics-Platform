## Celery workers

Background jobs: email receipts, inventory updates, restock alerts. Point `CELERY_BROKER_URL` at the Redis service from `infra/docker-compose.yml`.

```bash
pip install -r requirements.txt
celery -A celery_app worker --loglevel=INFO
```
