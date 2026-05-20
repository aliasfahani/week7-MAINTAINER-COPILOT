import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_mapping(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as handle:
        return {key.lower(): value for key, value in json.load(handle).items()}


def mapped_label(labels: list[str], mapping: dict[str, str]) -> str | None:
    for label in labels:
        normalized = label.lower().strip()
        if normalized in mapping:
            return mapping[normalized]
    return None


def split_time_ordered(rows: list[dict[str, Any]]) -> tuple[list, list, list]:
    total = len(rows)
    train_end = int(total * 0.70)
    val_end = int(total * 0.85)
    return rows[:train_end], rows[train_end:val_end], rows[val_end:]


def print_distribution(name: str, rows: list[dict[str, Any]]) -> None:
    counts = Counter(row["label"] for row in rows)
    print(f"{name}: {len(rows)} rows {dict(sorted(counts.items()))}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build classification dataset from GitHub issues.")
    parser.add_argument("--issues", default="data/raw/issues.jsonl")
    parser.add_argument("--mapping", default="data/processed/label_mapping.json")
    parser.add_argument("--output-dir", default="data/processed")
    args = parser.parse_args()

    issues = load_jsonl(Path(args.issues))
    mapping = load_mapping(Path(args.mapping))
    output_dir = Path(args.output_dir)

    dataset = []
    for issue in issues:
        label = mapped_label(issue.get("labels", []), mapping)
        if not label:
            continue
        sort_date = issue.get("closed_at") or issue.get("created_at") or ""
        dataset.append(
            {
                "id": issue["id"],
                "number": issue["number"],
                "label": label,
                "text": f"{issue.get('title', '')}\n\n{issue.get('body', '')}".strip(),
                "created_at": issue.get("created_at"),
                "closed_at": issue.get("closed_at"),
                "html_url": issue.get("html_url"),
                "sort_date": sort_date,
            }
        )

    dataset.sort(key=lambda row: row["sort_date"])
    train, val, test = split_time_ordered(dataset)

    write_jsonl(output_dir / "classification_dataset.jsonl", dataset)
    write_jsonl(output_dir / "train.jsonl", train)
    write_jsonl(output_dir / "val.jsonl", val)
    write_jsonl(output_dir / "test.jsonl", test)

    print_distribution("all", dataset)
    print_distribution("train", train)
    print_distribution("val", val)
    print_distribution("test", test)
    print("Split policy: train oldest 70%, val next 15%, test newest 15%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
