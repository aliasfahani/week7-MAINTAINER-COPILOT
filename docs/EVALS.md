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

The classifier itself is trained in Google Colab with:

```text
notebooks/pandas_issue_classifier_colab.ipynb
```

Copy the exported Colab files into `artifacts/classifier/` before running local evaluation.

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
  "question": "Installation conda install pandas pip install",
  "ideal_answer": "Use the pandas installation documentation.",
  "ground_truth_chunk_ids": ["docs-doc-source-getting_started-install.rst::s0w0"],
  "filters": {"source_type": "docs"}
}
```

The current golden set is aligned to real pandas chunks produced by `scripts/ingest_rag.py`.

Run RAG eval:

```bash
python3 evals/rag_eval.py
```

Reported metrics:

- hit@5
- MRR@10

Report path:

`artifacts/reports/rag_eval_report.json`

Latest local RAG eval after ingesting pandas docs/issues:

- examples: 6
- hit@5: 1.00
- MRR@10: 1.00

Current starter thresholds:

- hit@5 >= 0.40
- MRR@10 >= 0.20

The eval requires `data/processed/rag_chunks.jsonl`, which is produced by `scripts/ingest_rag.py`.

## CI Behavior

CI always runs tests, redaction tests, compile checks, and Docker Compose config validation.

Classifier and RAG evals run only when their required generated files/artifacts are present. This keeps CI practical without forcing a model training job or committing large generated data.
