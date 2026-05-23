import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

LABELS = ["bug", "feature", "docs", "question"]
FEW_EXAMPLES_WARNING_AT = 5


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


def mapped_labels(labels: list[str], mapping: dict[str, str]) -> list[str]:
    matches = []
    for label in labels:
        normalized = label.lower().strip()
        if normalized in mapping:
            matches.append(mapping[normalized])
    # Keep assignment label order stable when an issue has multiple mapped
    # labels. That makes repeated dataset builds deterministic and easier to
    # explain than relying on alphabetical ordering.
    unique = set(matches)
    return [label for label in LABELS if label in unique]


def split_time_ordered(rows: list[dict[str, Any]]) -> tuple[list, list, list]:
    total = len(rows)
    train_end = int(total * 0.70)
    val_end = int(total * 0.85)
    return rows[:train_end], rows[train_end:val_end], rows[val_end:]


def print_distribution(name: str, rows: list[dict[str, Any]]) -> None:
    counts = Counter(row["label"] for row in rows)
    print(f"{name}: {len(rows)} rows {dict(sorted(counts.items()))}")
    missing = [label for label in LABELS if counts.get(label, 0) == 0]
    if missing:
        print(f"WARNING: {name} split is missing classes: {missing}")
    rare = {label: count for label, count in counts.items() if 0 < count < FEW_EXAMPLES_WARNING_AT}
    if rare:
        print(f"WARNING: {name} split has very small classes: {rare}")


def save_distributions(path: Path, splits: dict[str, list[dict[str, Any]]]) -> None:
    report = {
        name: {
            "total": len(rows),
            "labels": dict(sorted(Counter(row["label"] for row in rows).items())),
        }
        for name, rows in splits.items()
    }
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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
    warnings = Counter()
    for issue in issues:
        labels = mapped_labels(issue.get("labels", []), mapping)
        if not labels:
            warnings["no_mapped_label"] += 1
            continue
        if len(labels) > 1:
            # Multi-label issues are common on GitHub. The classifier is
            # single-label, so Day 2 picks the first stable label but makes the
            # ambiguity visible for dataset review.
            warnings["multiple_mapped_labels"] += 1
        label = labels[0]
        sort_date = issue.get("closed_at") or issue.get("created_at") or ""
        dataset.append(
            {
                "id": issue["id"],
                "number": issue["number"],
                "label": label,
                "title": issue.get("title", ""),
                "body": issue.get("body", ""),
                "text": f"{issue.get('title', '')}\n\n{issue.get('body', '')}".strip(),
                "created_at": issue.get("created_at"),
                "closed_at": issue.get("closed_at"),
                "html_url": issue.get("html_url"),
                "sort_date": sort_date,
                "source_repo": "pandas-dev/pandas",
                "source_labels": issue.get("labels", []),
            }
        )

    dataset.sort(key=lambda row: row["sort_date"])
    train, val, test = split_time_ordered(dataset)

    write_jsonl(output_dir / "classification_dataset.jsonl", dataset)
    write_jsonl(output_dir / "train.jsonl", train)
    write_jsonl(output_dir / "val.jsonl", val)
    write_jsonl(output_dir / "test.jsonl", test)
    save_distributions(
        output_dir / "label_distributions.json",
        {"all": dataset, "train": train, "val": val, "test": test},
    )

    print_distribution("all", dataset)
    print_distribution("train", train)
    print_distribution("val", val)
    print_distribution("test", test)
    if warnings:
        print(f"Dataset warnings: {dict(sorted(warnings.items()))}")
    print("Split policy: train oldest 70%, val next 15%, test newest 15%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
