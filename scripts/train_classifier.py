import json
from collections import Counter
from pathlib import Path


TRAIN_PATH = Path("data/processed/train.jsonl")
VAL_PATH = Path("data/processed/val.jsonl")
MODEL_OUTPUT_DIR = Path("models/issue-classifier")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset split: {path}")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def describe_split(name: str, rows: list[dict]) -> None:
    counts = Counter(row["label"] for row in rows)
    print(f"{name}: {len(rows)} rows {dict(sorted(counts.items()))}")


def main() -> int:
    train = load_jsonl(TRAIN_PATH)
    val = load_jsonl(VAL_PATH)

    describe_split("train", train)
    describe_split("val", val)
    print(f"Future fine-tuned model output: {MODEL_OUTPUT_DIR}")
    print("TODO: fine-tune a small transformer such as DistilBERT on train/val.")
    print("TODO: save metrics, confusion matrix, and model card after evaluation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
