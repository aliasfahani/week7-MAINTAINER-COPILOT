import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.rag_service import search_hybrid


def load_jsonl(path: Path, name: str) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def reciprocal_rank(results: list[dict], truth: set[str], limit: int) -> float:
    for index, result in enumerate(results[:limit], start=1):
        if result["chunk_id"] in truth:
            return 1.0 / index
    return 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality.")
    parser.add_argument("--golden", default="data/golden/rag_golden.jsonl")
    parser.add_argument("--chunks", default="data/processed/rag_chunks.jsonl")
    parser.add_argument("--thresholds", default="evals/eval_thresholds.yaml")
    parser.add_argument("--output", default="artifacts/reports/rag_eval_report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    golden = load_jsonl(Path(args.golden), "RAG golden set")
    chunks = load_jsonl(Path(args.chunks), "RAG chunks file")
    if not chunks:
        raise SystemExit("RAG chunks are missing. Run scripts/ingest_rag.py first.")

    hits = 0
    reciprocal_ranks = []
    rows = []
    for example in golden:
        truth = set(example.get("ground_truth_chunk_ids", []))
        response = search_hybrid(
            example["question"],
            top_k=10,
            filters=example.get("filters") or None,
            chunks=chunks,
        )
        results = response["results"]
        hit = any(result["chunk_id"] in truth for result in results[:5])
        hits += int(hit)
        rr = reciprocal_rank(results, truth, limit=10)
        reciprocal_ranks.append(rr)
        rows.append(
            {
                "question": example["question"],
                "hit_at_5": hit,
                "reciprocal_rank": rr,
                "returned_chunk_ids": [result["chunk_id"] for result in results[:10]],
                "ground_truth_chunk_ids": list(truth),
            }
        )

    metrics = {
        "hit_at_5": hits / len(golden) if golden else 0.0,
        "mrr_at_10": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0,
        "num_examples": len(golden),
        "failed_examples": [row for row in rows if not row["hit_at_5"]],
        "examples": rows,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    thresholds = yaml.safe_load(Path(args.thresholds).read_text(encoding="utf-8")).get("rag", {})
    failures = []
    if metrics["hit_at_5"] < thresholds.get("hit_at_5_min", 0.0):
        failures.append(f"hit@5 {metrics['hit_at_5']:.3f} below threshold")
    if metrics["mrr_at_10"] < thresholds.get("mrr_at_10_min", 0.0):
        failures.append(f"MRR@10 {metrics['mrr_at_10']:.3f} below threshold")

    print(json.dumps({key: metrics[key] for key in ["hit_at_5", "mrr_at_10"]}, indent=2))
    print(f"Saved RAG eval report to {output}")
    if failures:
        print("RAG eval failed thresholds:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        print(f"RAG eval cannot run: {exc}. Run scripts/ingest_rag.py first.", file=sys.stderr)
        raise SystemExit(1)
