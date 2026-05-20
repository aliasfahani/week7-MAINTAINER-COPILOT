import argparse
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
    # New Day 2 datasets keep title/body separately. Older Day 1 datasets only
    # have text, so this remains backward compatible while preferring structure.
    title = row.get("title", "")
    body = row.get("body", "")
    return f"{title}\n\n{body}".strip() or row.get("text", "")


def label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["label"] for row in rows).items()))


def validate_labels(rows: list[dict[str, Any]], split_name: str) -> None:
    labels = {row.get("label") for row in rows}
    unknown = sorted(label for label in labels if label not in LABEL_TO_ID)
    if unknown:
        raise ValueError(f"{split_name} contains unknown labels: {unknown}. Expected {LABELS}")


def import_training_dependencies():
    try:
        import numpy as np
        import torch
        from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
        from torch.utils.data import Dataset
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise SystemExit(
            "Training dependencies are missing. Install them with:\n"
            "  pip install -r requirements.txt\n"
            f"Original import error: {exc}"
        ) from exc

    return {
        "np": np,
        "torch": torch,
        "Dataset": Dataset,
        "accuracy_score": accuracy_score,
        "confusion_matrix": confusion_matrix,
        "f1_score": f1_score,
        "AutoModelForSequenceClassification": AutoModelForSequenceClassification,
        "AutoTokenizer": AutoTokenizer,
        "Trainer": Trainer,
        "TrainingArguments": TrainingArguments,
    }


def build_dataset_class(torch, Dataset):
    class IssueDataset(Dataset):
        def __init__(self, encodings: dict[str, list[list[int]]], labels: list[int]):
            self.encodings = encodings
            self.labels = labels

        def __len__(self) -> int:
            return len(self.labels)

        def __getitem__(self, index: int) -> dict[str, Any]:
            # Trainer expects tensors for each tokenized field plus a labels key.
            item = {key: torch.tensor(value[index]) for key, value in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[index])
            return item

    return IssueDataset


def compute_metric_bundle(predictions, labels, deps: dict[str, Any]) -> dict[str, Any]:
    np = deps["np"]
    f1_score = deps["f1_score"]
    accuracy_score = deps["accuracy_score"]
    confusion_matrix = deps["confusion_matrix"]

    pred_ids = np.argmax(predictions, axis=1)
    per_class = f1_score(labels, pred_ids, average=None, labels=list(range(len(LABELS))), zero_division=0)
    return {
        "accuracy": float(accuracy_score(labels, pred_ids)),
        "macro_f1": float(f1_score(labels, pred_ids, average="macro", zero_division=0)),
        "per_class_f1": {label: float(score) for label, score in zip(LABELS, per_class, strict=True)},
        "confusion_matrix": confusion_matrix(labels, pred_ids, labels=list(range(len(LABELS)))).tolist(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune a transformer issue classifier.")
    parser.add_argument("--train-path", default="data/processed/train.jsonl")
    parser.add_argument("--val-path", default="data/processed/val.jsonl")
    parser.add_argument("--output-dir", default="artifacts/classifier")
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--epochs", type=float, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_rows = load_jsonl(Path(args.train_path))
    val_rows = load_jsonl(Path(args.val_path))
    validate_labels(train_rows, "train")
    validate_labels(val_rows, "val")

    print(f"train: {len(train_rows)} rows {label_counts(train_rows)}")
    print(f"val: {len(val_rows)} rows {label_counts(val_rows)}")
    if not train_rows or not val_rows:
        raise ValueError("Train and validation splits must both contain at least one row.")

    deps = import_training_dependencies()
    tokenizer = deps["AutoTokenizer"].from_pretrained(args.model_name)

    train_texts = [issue_text(row) for row in train_rows]
    val_texts = [issue_text(row) for row in val_rows]
    train_labels = [LABEL_TO_ID[row["label"]] for row in train_rows]
    val_labels = [LABEL_TO_ID[row["label"]] for row in val_rows]

    # Tokenization controls model cost and truncates very long issue threads.
    # max_length=256 is a practical Day 2 default for laptop-friendly training.
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=args.max_length)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=args.max_length)
    IssueDataset = build_dataset_class(deps["torch"], deps["Dataset"])

    model = deps["AutoModelForSequenceClassification"].from_pretrained(
        args.model_name,
        num_labels=len(LABELS),
        id2label={index: label for label, index in LABEL_TO_ID.items()},
        label2id=LABEL_TO_ID,
    )

    training_args = deps["TrainingArguments"](
        output_dir=str(output_dir / "checkpoints"),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        logging_steps=20,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        report_to=[],
    )

    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        metrics = compute_metric_bundle(predictions, labels, deps)
        # Trainer metric names must be flat scalars.
        return {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            **{f"f1_{label}": score for label, score in metrics["per_class_f1"].items()},
        }

    trainer = deps["Trainer"](
        model=model,
        args=training_args,
        train_dataset=IssueDataset(train_encodings, train_labels),
        eval_dataset=IssueDataset(val_encodings, val_labels),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    eval_output = trainer.predict(IssueDataset(val_encodings, val_labels))
    metrics = compute_metric_bundle(eval_output.predictions, eval_output.label_ids, deps)

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    (output_dir / "label_mapping.json").write_text(
        json.dumps({"label_to_id": LABEL_TO_ID, "id_to_label": ID_TO_LABEL}, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (output_dir / "training_config.json").write_text(
        json.dumps(
            {
                "base_model": args.model_name,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "max_length": args.max_length,
                "learning_rate": args.learning_rate,
                "train_path": args.train_path,
                "val_path": args.val_path,
                "train_size": len(train_rows),
                "val_size": len(val_rows),
                "labels": LABELS,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metrics, indent=2))
    print(f"Saved classifier artifact to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
