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

The model server is a separate FastAPI service. It exposes `/health`, classifier inference when a trained artifact exists, rule-based NER, and simple extractive summarization.

## Day 4 Flow

```text
Streamlit / React widget / API client
  -> FastAPI routes
  -> services
  -> repositories
  -> infra
```

Authentication uses JWT bearer tokens. Password hashing and token creation live in `auth_service`, while routes only validate inputs and return responses.

Chat uses one tool-calling design. In local fallback mode, a deterministic planner chooses from the same tool list so the app can be demoed without an LLM key. This fallback is not a multi-agent system.

Short-term conversation state is stored in Redis with a 24-hour TTL. If Redis is unavailable during local tests, an in-process fallback is used.

Long-term semantic memory is stored in Postgres and every memory write creates an audit log row.

Widget configuration is stored in Postgres. Public widget config checks the request origin against the widget allowlist before returning safe fields.

Day 5 adds a public widget chat endpoint that reuses the same chat service but validates widget origin first. It uses a synthetic widget user so public widget traffic does not access normal authenticated user memory.
