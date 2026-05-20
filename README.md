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
