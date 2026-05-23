# Model Card

## Model Name

Maintainer's Copilot issue classifier.

## Base Architecture

`distilbert-base-uncased`.

## Task

Classify GitHub issues into one of four maintainer triage labels:

- `bug`
- `feature`
- `docs`
- `question`

## Dataset Source

Closed GitHub issues from `pandas-dev/pandas`.

## Split Policy

Time-based split from `scripts/build_dataset.py`:

- train: oldest 70%
- validation: next 15%
- test: newest 15%

This avoids training on newer issues and testing on older ones.

## Label Mapping

Editable mapping lives in `data/processed/label_mapping.json`.

Starter examples:

- pandas `bug` -> `bug`
- pandas `enhancement` -> `feature`
- pandas `Docs` -> `docs`
- pandas `Usage Question` -> `question`

## Training Data Counts

Current local pandas dataset from `scripts/fetch_issues.py --per-label-limit 500` and `scripts/build_dataset.py`:

- all: 1,962 rows
- train: 1,373 rows (`bug`: 519, `feature`: 444, `docs`: 280, `question`: 130)
- validation: 294 rows (`bug`: 6, `feature`: 7, `docs`: 71, `question`: 210)
- test: 295 rows (`bug`: 9, `feature`: 35, `docs`: 116, `question`: 135)

The validation/test splits are newer than train, but label balance is uneven because pandas label usage changed over time.

## Hyperparameters

Default training settings:

- base model: `distilbert-base-uncased`
- epochs: `2`
- batch size: `8`
- max sequence length: `256`
- learning rate: `2e-5`
- weight decay: `0.01`

These are intentionally lightweight for a Colab T4 GPU workflow.

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

- No real model is available locally until the Colab artifact is copied into `artifacts/classifier/`.
- GitHub labels can be noisy or inconsistent.
- Multi-label issues are collapsed into a single label for this classifier.
- Small classes may produce weak per-class F1.
- Long issue threads are truncated to the configured max sequence length.

## Reproduce Training

```bash
make fetch-issues
make build-dataset
```

Then open and run:

`notebooks/pandas_issue_classifier_colab.ipynb`

Copy the exported Colab files into `artifacts/classifier/`.

## Reproduce Evaluation

```bash
python3 scripts/evaluate_classifier.py \
  --model-dir artifacts/classifier \
  --test-path data/processed/test.jsonl
```
