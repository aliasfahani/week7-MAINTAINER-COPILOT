import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.classifier_common import LABELS, LABEL_TO_ID, import_inference_dependencies, issue_text, load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a saved issue classifier on the test split.")
    parser.add_argument("--model-dir", default="artifacts/classifier")
    parser.add_argument("--test-path", default="data/processed/test.jsonl")
    parser.add_argument("--output", default="artifacts/reports/classifier_test_metrics.json")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=256)
    return parser.parse_args()


def validate_artifact(model_dir: Path) -> None:
    required = ["config.json", "label_mapping.json"]
    missing = [name for name in required if not (model_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Classifier artifact is incomplete at {model_dir}. Missing: {missing}. "
            "Run the Colab notebook and copy its exported files into artifacts/classifier first."
        )


def compute_metrics(pred_ids: list[int], true_ids: list[int], deps: dict[str, Any]) -> dict[str, Any]:
    f1_score = deps["f1_score"]
    accuracy_score = deps["accuracy_score"]
    confusion_matrix = deps["confusion_matrix"]

    per_class = f1_score(true_ids, pred_ids, average=None, labels=list(range(len(LABELS))), zero_division=0)
    return {
        "accuracy": float(accuracy_score(true_ids, pred_ids)),
        "macro_f1": float(f1_score(true_ids, pred_ids, average="macro", zero_division=0)),
        "per_class_f1": {label: float(score) for label, score in zip(LABELS, per_class, strict=True)},
        "confusion_matrix": confusion_matrix(true_ids, pred_ids, labels=list(range(len(LABELS)))).tolist(),
        "labels": LABELS,
    }


def main() -> int:
    args = parse_args()
    model_dir = Path(args.model_dir)
    output_path = Path(args.output)
    validate_artifact(model_dir)

    test_rows = load_jsonl(Path(args.test_path))
    if not test_rows:
        raise ValueError(f"Test split is empty: {args.test_path}")

    deps = import_inference_dependencies()
    torch = deps["torch"]
    tokenizer = deps["AutoTokenizer"].from_pretrained(model_dir)
    model = deps["AutoModelForSequenceClassification"].from_pretrained(model_dir)
    model.eval()

    texts = [issue_text(row) for row in test_rows]
    true_ids = [LABEL_TO_ID[row["label"]] for row in test_rows]
    pred_ids = []

    with torch.no_grad():
        for start in range(0, len(texts), args.batch_size):
            batch_texts = texts[start : start + args.batch_size]
            encoded = tokenizer(
                batch_texts,
                truncation=True,
                padding=True,
                max_length=args.max_length,
                return_tensors="pt",
            )
            logits = model(**encoded).logits
            pred_ids.extend(torch.argmax(logits, dim=1).tolist())

    metrics = compute_metrics(pred_ids, true_ids, deps)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print("Classifier test metrics")
    print(json.dumps(metrics, indent=2))
    print(f"Saved report to {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as exc:
        print(f"Classifier evaluation cannot run: {exc}", file=sys.stderr)
        raise SystemExit(1)
