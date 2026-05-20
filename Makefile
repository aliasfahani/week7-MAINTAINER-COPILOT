.PHONY: up down logs migrate seed-vault fetch-issues build-dataset train-classifier eval-classifier model-server test-model-server test

OWNER ?= psf
REPO ?= requests
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

build-dataset:
	$(PYTHON) scripts/build_dataset.py

train-classifier:
	$(PYTHON) scripts/train_classifier.py

eval-classifier:
	$(PYTHON) scripts/evaluate_classifier.py

model-server:
	uvicorn model_server.main:app --host 0.0.0.0 --port 8001

test-model-server:
	$(PYTHON) -m pytest tests/test_model_server.py

test:
	$(PYTHON) -m pytest
