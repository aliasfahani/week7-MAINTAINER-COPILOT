.PHONY: up up-detached down logs migrate seed-vault seed-admin fetch-issues fetch-docs build-dataset ingest-rag ingest-rag-db train-classifier eval-classifier eval-rag eval-all smoke-test model-server streamlit widget-dev host chat-test test-model-server test

OWNER ?= pandas-dev
REPO ?= pandas
BRANCH ?= main
PYTHON ?= python3

up:
	docker compose up --build

up-detached:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm migrate

seed-vault:
	$(PYTHON) scripts/seed_vault.py

seed-admin:
	$(PYTHON) scripts/seed_admin.py

fetch-issues:
	$(PYTHON) scripts/fetch_issues.py --owner $(OWNER) --repo $(REPO) --output data/raw/issues.jsonl

fetch-docs:
	$(PYTHON) scripts/fetch_docs.py --owner $(OWNER) --repo $(REPO) --branch $(BRANCH)

build-dataset:
	$(PYTHON) scripts/build_dataset.py

ingest-rag:
	$(PYTHON) scripts/ingest_rag.py --repo $(OWNER)/$(REPO)

ingest-rag-db:
	$(PYTHON) scripts/ingest_rag.py --repo $(OWNER)/$(REPO) --store-db

train-classifier:
	$(PYTHON) scripts/train_classifier.py

eval-classifier:
	$(PYTHON) scripts/evaluate_classifier.py

eval-rag:
	$(PYTHON) evals/rag_eval.py

eval-all:
	$(PYTHON) evals/classification_eval.py || true
	$(PYTHON) evals/rag_eval.py || true

smoke-test:
	$(PYTHON) scripts/smoke_test.py

model-server:
	uvicorn model_server.main:app --host 0.0.0.0 --port 8001

streamlit:
	streamlit run frontend/streamlit/app.py

widget-dev:
	cd frontend/widget && npm install && npm run dev -- --host 0.0.0.0

host:
	$(PYTHON) -m http.server 8080 --directory frontend/host

chat-test:
	curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -H "Authorization: Bearer $$TOKEN" -d '{"message":"search docs for auth","issue":{"title":"auth bug","body":"JWT fails"}}'

test-model-server:
	$(PYTHON) -m pytest tests/test_model_server.py

test:
	$(PYTHON) -m pytest
