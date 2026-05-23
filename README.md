# Maintainer's Copilot

Maintainer's Copilot is a Week 7 project for helping open-source maintainers triage GitHub issues with classification, entity extraction, summarization, RAG, memory, and a single tool-calling LLM chatbot.

## Day 1 Status

Implemented:
- final folder structure
- FastAPI API `/health`
- model server `/health`
- placeholder `/classify`, `/ner`, and `/summarize`
- Docker Compose for API, model server, Postgres + pgvector, Redis, MinIO, Vault, and migrations
- Alembic baseline for `users`, `documents`, and `chunks`
- Vault development seeding script
- GitHub issue fetch script
- label mapping and classification dataset builder
- classifier training skeleton
- initial architecture and decision docs

## Day 2 Status

Implemented:
- Colab-based DistilBERT fine-tuning workflow for issue classification
- test-set evaluation script with accuracy, macro-F1, per-class F1, and confusion matrix
- threshold-gated classification eval entry point
- model server classifier inference path using `artifacts/classifier/` when available
- controlled `/classify` 503 response when the trained model is missing
- practical rule-based `/ner`
- simple extractive `/summarize`
- main API model server client
- classifier, NER, and summarizer tool wrappers
- service-level chat action proof for `classify`

Still not implemented:
- full chatbot orchestration
- RAG
- memory
- Streamlit UI
- React widget behavior

## Day 3 Status

Implemented:
- GitHub documentation fetch script
- RAG corpus builder from docs and closed issues
- structure-aware chunking
- embedding helper with SentenceTransformers and deterministic fallback
- local JSONL chunk store plus optional Postgres/pgvector storage
- dense retrieval
- sparse BM25-style retrieval
- hybrid retrieval with simple reranking
- metadata filters
- `rag_search_tool`
- local retrieved chunk snapshots
- pandas-aligned RAG golden set and retrieval eval

Still not implemented:
- LLM-powered query rewrite
- MinIO upload for snapshots
- Postgres/pgvector storage verification when Docker is unavailable

## Quickstart

```bash
cp .env.example .env
make up-detached
make seed-vault
make migrate
make seed-admin
curl http://localhost:8000/health
curl http://localhost:8001/health
```

Use `make up` if you want foreground logs. Use `make down` to stop services.

Fetch pandas issues and build the classifier dataset:

```bash
make fetch-issues
make build-dataset
```

The dataset comes from `pandas-dev/pandas` closed issues. The label mapping is:

- GitHub `bug` -> assignment `bug`
- GitHub `enhancement` -> assignment `feature`
- GitHub `Docs` -> assignment `docs`
- GitHub `Usage Question` -> assignment `question`

Train the classifier in Google Colab:

```text
notebooks/pandas_issue_classifier_colab.ipynb
```

After Colab exports `classifier_artifact.zip`, unzip it so the files are directly inside:

```text
artifacts/classifier/
```

Then evaluate classifier locally:

```bash
make eval-classifier
```

Run the model server locally:

```bash
make model-server
```

Example classify request:

```bash
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{"title":"Login fails in production","body":"JWT token is invalid after deploy"}'
```

Before the Colab artifact is copied into `artifacts/classifier/`, `/classify` returns a controlled `503` explaining that the classifier artifact is missing.

Fetch docs:

```bash
make fetch-docs
```

Build local RAG corpus and chunks:

```bash
make ingest-rag
```

Store RAG chunks in Postgres/pgvector after services and migrations are running:

```bash
make ingest-rag-db
```

Run RAG eval:

```bash
make eval-rag
```

## Day 4 Status

Implemented:
- JWT auth with user/admin roles
- `/auth/register`, `/auth/login`, `/auth/me`
- authenticated `/chat`
- single tool-calling design with local fallback planner
- Redis short-term memory with TTL and local fallback
- Postgres semantic memory tables and audit logs
- `/memory` endpoints
- widget config API and `/widget.js` loader
- simple Streamlit login/chat/memory/widget admin app
- simple React embeddable widget and demo host page

Run admin seed:

```bash
make seed-admin
```

Run Streamlit:

```bash
make streamlit
```

Run widget dev server:

```bash
make widget-dev
```

Run host demo:

```bash
make host
```

Chat endpoint example:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Classify this issue and search similar resolved issues","issue":{"title":"JWT fails","body":"Invalid token after deploy"}}'
```

Current limitation: the React widget UI can load config and send a request, but authenticated chat requires a JWT. A public widget chat proxy is a recommended Day 5 polish item.

## Day 5 Status

Polished:
- smoke test script
- practical CI checks
- redaction tests
- public widget chat endpoint with origin validation
- README/runbook/demo/submission docs

Run smoke test after the stack is up, Vault is seeded, migrations ran, and admin is seeded:

```bash
make smoke-test
```

Run all local checks:

```bash
python3 -m pytest
docker compose config
python3 -m compileall app model_server scripts evals tests
```

## Submission Docs

- `docs/ARCH.md`
- `docs/DECISIONS.md`
- `docs/RUNBOOK.md`
- `docs/EVALS.md`
- `docs/SECURITY.md`
- `docs/DEMO_SCRIPT.md`
- `docs/SUBMISSION.md`
