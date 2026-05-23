import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run classifier eval and enforce thresholds.")
    parser.add_argument("--model-dir", default="artifacts/classifier")
    parser.add_argument("--test-path", default="data/processed/test.jsonl")
    parser.add_argument("--thresholds", default="evals/eval_thresholds.yaml")
    parser.add_argument("--report", default="artifacts/reports/classifier_test_metrics.json")
    return parser.parse_args()


def load_thresholds(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("classification", {})


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)

    command = [
        sys.executable,
        "scripts/evaluate_classifier.py",
        "--model-dir",
        args.model_dir,
        "--test-path",
        args.test_path,
        "--output",
        args.report,
    ]
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        print(
            "Classifier evaluation failed. Run the Colab notebook and copy artifacts into "
            "artifacts/classifier before running CI evals.",
            file=sys.stderr,
        )
        return completed.returncode

    metrics = json.loads(report_path.read_text(encoding="utf-8"))
    thresholds = load_thresholds(Path(args.thresholds))
    failures = []

    for metric_name in ["accuracy", "macro_f1"]:
        threshold = thresholds.get(f"{metric_name}_min")
        if threshold is not None and metrics.get(metric_name, 0.0) < threshold:
            failures.append(f"{metric_name}={metrics.get(metric_name):.4f} < required {threshold:.4f}")

    if failures:
        print("Classifier eval failed thresholds:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Classifier eval passed thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
