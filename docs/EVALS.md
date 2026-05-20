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

RAG retrieval metrics:
- hit@5
- MRR@10

RAG retrieval eval is now available.

Golden set format in `data/golden/rag_golden.jsonl`:

```json
{
  "question": "How do I configure authentication tokens?",
  "ideal_answer": "Use the authentication documentation.",
  "ground_truth_chunk_ids": ["docs-readme.md::s0w0"],
  "filters": {}
}
```

Run RAG eval:

```bash
python3 evals/rag_eval.py
```

Reported metrics:

- hit@5
- MRR@10

Report path:

`artifacts/reports/rag_eval_report.json`

Current starter thresholds:

- hit@5 >= 0.40
- MRR@10 >= 0.20

The eval requires `data/processed/rag_chunks.jsonl`, which is produced by `scripts/ingest_rag.py`.
