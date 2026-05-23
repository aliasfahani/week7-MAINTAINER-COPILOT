# Demo Script

## 10-Minute Flow

1. Problem and goal  
   Maintainers need help triaging issues, finding related resolved issues, and remembering project context.

2. Architecture overview  
   Show `docs/ARCH.md`: FastAPI API, model server, Postgres/pgvector, Redis, Vault, MinIO, Streamlit, React widget.

3. Dataset and label mapping  
   Show `data/processed/label_mapping.json` and the GitHub issue fetch/build scripts.

4. Classifier demo/results  
   Explain DistilBERT training/eval scripts. If no trained artifact exists, show controlled `/classify` missing-model response.

5. RAG demo/results  
   Run docs/issues ingestion, inspect `rag_chunks.jsonl`, and run `make eval-rag` when chunks exist.

6. Chatbot demo  
   Login, call `/chat`, and show `tool_calls` plus `trace_id`.

7. Memory demo  
   Use Streamlit memory inspector or `POST /memory`; explain audit log creation.

8. Widget embed demo  
   Run widget dev server and host page. Show the script tag using `/widget.js`.

9. Evals/CI demo  
   Show `.github/workflows/ci.yml`, tests, optional eval conditions, and thresholds.

10. Observability/redaction demo  
    Show redaction tests and trace IDs in chat responses/logs.

11. Known limitations and next steps  
    Real LLM key, trained classifier artifact, live pgvector verification, and production widget auth are next.

## Commands

```bash
cp .env.example .env
make up-detached
make seed-vault
make migrate
make seed-admin
python3 -m pytest
make smoke-test
make streamlit
make widget-dev
make host
```

Health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

Login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```
