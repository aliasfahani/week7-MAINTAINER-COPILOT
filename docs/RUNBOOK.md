# Runbook

## Day 1 Local Flow

1. Copy `.env.example` to `.env`.
2. Start services in the background with `make up-detached`.
3. Seed Vault with `make seed-vault`.
4. Run migrations with `make migrate`.
5. Seed admin with `make seed-admin`.
6. Check API health at `http://localhost:8000/health`.
7. Check model server health at `http://localhost:8001/health`.
8. Run `make smoke-test`.

## Day 4 Local Flow

Run migrations and seed an admin:

```bash
make migrate
make seed-admin
```

Default admin:

```text
admin@example.com / admin123
```

Run Streamlit:

```bash
make streamlit
```

Run the React widget dev server:

```bash
make widget-dev
```

Run the demo host page:

```bash
make host
```

Embed snippet:

```html
<script src="http://localhost:8000/widget.js" data-widget-id="demo-widget"></script>
```

## Common Fixes

- Docker daemon not running: start Docker Desktop, then rerun `make up-detached`.
- Vault seed fails: confirm Vault is running at `http://localhost:8200`.
- Admin seed fails: run `make migrate` first.
- Classifier eval fails: run `notebooks/pandas_issue_classifier_colab.ipynb`, copy the exported files into `artifacts/classifier/`, then rerun `make eval-classifier`.
- RAG eval fails: run `make fetch-docs`, `make fetch-issues`, and `make ingest-rag` first.

## Logs And Tracing

Chat responses include `trace_id`. Tool calls create structured log spans. There is no tracing UI yet; use Docker/API logs:

```bash
make logs
```
