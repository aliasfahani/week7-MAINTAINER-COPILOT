# Model Card

## Model Name

Maintainer's Copilot issue classifier.

## Base Architecture

`distilbert-base-uncased` by default.

## Task

Classify GitHub issues into one of four maintainer triage labels:

- `bug`
- `feature`
- `docs`
- `question`

## Dataset Source

TBD. Day 1/Day 2 scripts support fetching closed GitHub issues from a selected repository with `scripts/fetch_issues.py`.

## Split Policy

Time-based split from `scripts/build_dataset.py`:

- train: oldest 70%
- validation: next 15%
- test: newest 15%

This avoids training on newer issues and testing on older ones.

## Label Mapping

Editable mapping lives in `data/processed/label_mapping.json`.

Starter examples:

- `bug`, `type: bug` -> `bug`
- `enhancement`, `feature`, `feature request` -> `feature`
- `documentation`, `docs` -> `docs`
- `question`, `support` -> `question`

## Training Data Counts

TBD until real issues are fetched and `scripts/build_dataset.py` is run.

## Hyperparameters

Default training settings:

- base model: `distilbert-base-uncased`
- epochs: `2`
- batch size: `8`
- max sequence length: `256`
- learning rate: `2e-5`
- weight decay: `0.01`

These are intentionally lightweight for a laptop-friendly Week 7 workflow.

## Validation Metrics

TBD until training runs.

Saved after training to:

`artifacts/classifier/metrics.json`

Metrics include:

- accuracy
- macro-F1
- per-class F1
- confusion matrix

## Test Metrics

TBD until evaluation runs.

Saved after evaluation to:

`artifacts/reports/classifier_test_metrics.json`

## Artifact Location

Trained classifier artifacts are saved to:

`artifacts/classifier/`

Expected contents include:

- Hugging Face model files
- tokenizer files
- `label_mapping.json`
- `metrics.json`
- `training_config.json`

## Intended Use

The classifier is intended to help maintainers triage GitHub issues quickly by predicting a likely issue category.

## Not Intended Use

The classifier should not be treated as an authoritative moderation, security, or project governance decision-maker. Maintainers should review predictions before acting on them.

## Known Limitations

- No real model is trained until a repository is chosen and dataset splits are generated.
- GitHub labels can be noisy or inconsistent.
- Multi-label issues are collapsed into a single label for this classifier.
- Small classes may produce weak per-class F1.
- Long issue threads are truncated to the configured max sequence length.

## Reproduce Training

```bash
python3 scripts/train_classifier.py \
  --train-path data/processed/train.jsonl \
  --val-path data/processed/val.jsonl \
  --output-dir artifacts/classifier
```

## Reproduce Evaluation

```bash
python3 scripts/evaluate_classifier.py \
  --model-dir artifacts/classifier \
  --test-path data/processed/test.jsonl
```
