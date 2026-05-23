## API service

REST + Strawberry GraphQL. WebSocket endpoints for dashboards should stream derived metrics sourced from Redis or a dedicated projections table.

Run locally:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
