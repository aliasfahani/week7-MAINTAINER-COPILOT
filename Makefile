.PHONY: up down logs migrate seed-vault fetch-issues fetch-docs build-dataset ingest-rag ingest-rag-db train-classifier eval-classifier eval-rag model-server test-model-server test

OWNER ?= psf
REPO ?= requests
BRANCH ?= main
PYTHON ?= python3

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm migrate

seed-vault:
	$(PYTHON) scripts/seed_vault.py

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

model-server:
	uvicorn model_server.main:app --host 0.0.0.0 --port 8001

test-model-server:
	$(PYTHON) -m pytest tests/test_model_server.py

test:
	$(PYTHON) -m pytest
