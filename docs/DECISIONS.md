# Decisions

## Day 1

- Chosen GitHub repo: TBD.
- Why this repo: TBD after inspecting labels and closed issue volume.
- Label mapping: GitHub issue labels are mapped into `bug`, `feature`, `docs`, and `question` through `data/processed/label_mapping.json`.
- Split policy: time-based split. The oldest 70% of mapped issues are train, the next 15% are validation, and the newest 15% are test.
- Initial model choice: DistilBERT or a similar small transformer so training remains practical for a Week 7 project.
- RAG plan: use project docs plus resolved issues and maintainer answers. Start with clean chunking and pgvector, then add hybrid retrieval and reranking later if time allows.
- Chatbot architecture: one tool-calling LLM. Tools may call classifier, NER, summarization, RAG, and memory, but there will be no multi-agent system.

## Day 2

- Base classifier model: `distilbert-base-uncased`.
- Why this model: it is a small transformer with good Hugging Face support and is practical for a student laptop or small cloud instance.
- Classifier status: real fine-tuning and test evaluation scripts are implemented, but metrics remain TBD until real dataset splits are generated and training runs.
- Label mapping notes: mapping stays editable in `data/processed/label_mapping.json`; multi-label issues are warned about and collapsed to one label for this single-label classifier.
- Split policy: still time-based, with newest issues reserved for test.
- NER approach: Day 2 uses practical regex/rule-based extraction for files, versions, errors, function names, and code identifiers. This is intentionally simple and replaceable later.
- Summarization approach: Day 2 uses simple extractive summarization by keeping the first few meaningful sentences and capping length.
- API/model boundary: model inference lives in `model_server`; the main API calls it through `app/infra/model_client.py` and exposes service-level tool wrappers in `app/services/tool_service.py`.
- Known limitation: `/classify` returns a controlled 503 until `artifacts/classifier/` contains a trained model.

## Day 3

- RAG corpus sources: repository documentation fetched from README/docs/examples/changelog files plus closed GitHub issues from `data/raw/issues.jsonl`.
- Leakage policy: RAG uses closed issues for retrieval. Once the classifier dataset is generated for a chosen repo, we should avoid using classifier test issues as RAG eval ground truth where feasible.
- Chunking strategy: docs split by markdown headings first and fall back to overlapping character windows for long sections. Issues keep title/body/resolution context together.
- Embedding model choice: `sentence-transformers/all-MiniLM-L6-v2`, because it is small, common, and produces 384-dimensional embeddings suitable for pgvector. Day 3 defaults to the deterministic hash backend for tests/offline development; set `EMBEDDING_BACKEND=sentence-transformers` to use the real model.
- Storage strategy: chunks are written to `data/processed/rag_chunks.jsonl` for debugging and can also be stored in Postgres using pgvector with `scripts/ingest_rag.py --store-db`.
- Sparse retrieval: compact BM25-style scoring implemented in code, useful for exact terms like `auth.py`, `TypeError`, versions, and config keys.
- Hybrid scoring: default weight is 0.6 dense and 0.4 sparse.
- Metadata filtering: supports `source_type`, `repo`, `label`, and `issue_number`.
- Reranking strategy: simple heuristic boost for exact query-term matches and title matches. This is intentionally explainable and can be replaced with a cross-encoder later.
- Retrieved chunk snapshots: Day 3 saves local JSON snapshots under `artifacts/rag-snapshots/`; MinIO upload is still TODO.
- Known limitation: full query rewriting is prompt-only for now, not wired to an LLM call.

## Day 4

- Auth choice: JWT bearer tokens with PBKDF2 password hashing. The JWT signing key is read from Vault when available, with a local development fallback for tests.
- Roles: `user` and `admin`. Admin-only widget configuration uses the `require_admin` dependency.
- Chatbot design: one tool-calling LLM architecture. Day 4 includes a documented deterministic fallback planner for local demos when no LLM API key is available.
- Tool failure behavior: failed tools return structured errors and do not crash the whole chat response.
- Redis TTL: short-term conversation memory uses a 24-hour TTL (`86400` seconds), which is long enough for a workday but avoids stale temporary context.
- Semantic memory: long-term memory stores redacted text and embeddings in Postgres. Memory writes are explicit through `write_memory`.
- Audit logs: every long-term memory write creates an `audit_logs` row.
- Widget config: stored in Postgres with `allowed_origins`, theme, greeting, and enabled tools.
- Origin checks: public widget config checks `Origin` or `Referer`. This is a simple allowlist and should be hardened later with deployment-specific CORS/CSP.
- Widget loader: FastAPI serves `/widget.js`, which injects an iframe pointing to the React widget dev URL.
