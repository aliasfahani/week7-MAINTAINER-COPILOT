# Evals

Planned classification metrics:
- accuracy
- macro-F1
- per-class F1
- confusion matrix

Run classifier evaluation:

```bash
python3 scripts/evaluate_classifier.py
```

Run threshold-gated classifier eval:

```bash
python3 evals/classification_eval.py
```

Classifier reports are saved to:

`artifacts/reports/classifier_test_metrics.json`

Current starter thresholds in `evals/eval_thresholds.yaml`:

- accuracy >= 0.50
- macro-F1 >= 0.50

The eval fails clearly if the trained model artifact does not exist.

Planned RAG metrics:
- hit@5
- MRR@10

RAG evals are still planned for a later day.
