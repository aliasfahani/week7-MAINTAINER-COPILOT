# Architecture

Day 1 establishes the project foundation without building full product features.

```text
frontend clients
  -> FastAPI API
    -> routes
    -> services
    -> repositories
    -> infra/database

FastAPI API -> model_server
FastAPI API -> Postgres + pgvector
FastAPI API -> Redis
FastAPI API -> MinIO
FastAPI API -> Vault

scripts -> GitHub API -> data/raw -> data/processed
```

Routes stay thin. Business logic belongs in services, database access in repositories, and external systems in `app/infra`.

The model server is a separate FastAPI service. It exposes `/health` and Day 1 placeholder NLP endpoints for classification, NER, and summarization.
