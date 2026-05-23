import json
from collections import Counter
from pathlib import Path
from typing import Any

LABELS = ["bug", "feature", "docs", "question"]
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}
ID_TO_LABEL = {str(index): label for label, index in LABEL_TO_ID.items()}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing dataset split: {path}. Run scripts/fetch_issues.py and scripts/build_dataset.py first."
        )
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def issue_text(row: dict[str, Any]) -> str:
    # Datasets keep title/body separately, but older generated rows may only
    # have `text`. This helper keeps both formats usable for eval and notebooks.
    title = row.get("title", "")
    body = row.get("body", "")
    return f"{title}\n\n{body}".strip() or row.get("text", "")


def label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["label"] for row in rows).items()))


def import_inference_dependencies():
    try:
        import torch
        from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            "Classifier evaluation dependencies are missing. Install them with:\n"
            "  pip install -r requirements.txt\n"
            f"Original import error: {exc}"
        ) from exc

    return {
        "torch": torch,
        "accuracy_score": accuracy_score,
        "confusion_matrix": confusion_matrix,
        "f1_score": f1_score,
        "AutoModelForSequenceClassification": AutoModelForSequenceClassification,
        "AutoTokenizer": AutoTokenizer,
    }
