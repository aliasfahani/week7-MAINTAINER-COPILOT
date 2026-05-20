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
- DistilBERT fine-tuning script for issue classification
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

## Quickstart

```bash
cp .env.example .env
make up
make seed-vault
make migrate
curl http://localhost:8000/health
curl http://localhost:8001/health
```

Fetch issues after choosing a repo:

```bash
make fetch-issues OWNER=owner REPO=repo
make build-dataset
make train-classifier
```

Evaluate classifier:

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

Before training, `/classify` returns a controlled `503` explaining that the classifier artifact is missing.
