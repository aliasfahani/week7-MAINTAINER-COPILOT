.PHONY: up down logs migrate seed-vault fetch-issues build-dataset train-classifier test

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

test:
	$(PYTHON) -m pytest
