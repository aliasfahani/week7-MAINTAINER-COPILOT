import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.infra.embeddings import embed_texts
from app.services.rag_service import chunk_documents


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def issue_to_document(issue: dict[str, Any], repo: str | None = None) -> dict[str, Any]:
    number = issue.get("number")
    labels = issue.get("labels", [])
    text = (
        f"Title: {issue.get('title', '')}\n\n"
        f"Body:\n{issue.get('body', '')}\n\n"
        f"Resolution context: issue is {issue.get('state', 'closed')} and closed at {issue.get('closed_at')}."
    ).strip()
    return {
        "source_type": "issue",
        "source_id": f"issue_{number}",
        "title": issue.get("title", f"Issue {number}"),
        "url": issue.get("html_url"),
        "text": text,
        "metadata": {
            "issue_number": number,
            "labels": labels,
            "state": issue.get("state"),
            "created_at": issue.get("created_at"),
            "closed_at": issue.get("closed_at"),
            "repo": repo,
            "comments": issue.get("comments", 0),
            "leakage_policy": "RAG corpus built from closed issues; classifier test leakage avoidance is documented and should be enforced once a repo is chosen.",
        },
    }


def prepare_for_database(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared = []
    for row in rows:
        prepared.append(
            {
                **row,
                "metadata_json": json.dumps(row.get("metadata", {}), ensure_ascii=False),
                "embedding_json": json.dumps(row.get("embedding", [])),
            }
        )
    return prepared


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and optionally store the RAG corpus.")
    parser.add_argument("--docs-path", default="data/processed/rag_docs.jsonl")
    parser.add_argument("--issues-path", default="data/raw/issues.jsonl")
    parser.add_argument("--corpus-output", default="data/processed/rag_corpus.jsonl")
    parser.add_argument("--chunks-output", default="data/processed/rag_chunks.jsonl")
    parser.add_argument("--repo", default=None, help="Optional owner/repo metadata for issue rows.")
    parser.add_argument("--store-db", action="store_true", help="Store documents/chunks in Postgres/pgvector.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docs = load_jsonl(Path(args.docs_path))
    issues = load_jsonl(Path(args.issues_path))
    issue_documents = [
        issue_to_document(issue, repo=args.repo)
        for issue in issues
        if issue.get("state") == "closed" or issue.get("closed_at")
    ]
    documents = docs + issue_documents
    if not documents:
        raise SystemExit("No RAG documents found. Run scripts/fetch_docs.py and/or scripts/fetch_issues.py first.")

    chunks = chunk_documents(documents)
    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        chunk["embedding"] = embedding

    write_jsonl(Path(args.corpus_output), documents)
    write_jsonl(Path(args.chunks_output), chunks)
    print(f"Wrote {len(documents)} RAG documents to {args.corpus_output}")
    print(f"Wrote {len(chunks)} RAG chunks to {args.chunks_output}")

    if args.store_db:
        from app.infra.db import SessionLocal
        from app.repositories.documents import replace_rag_documents

        db = SessionLocal()
        try:
            replace_rag_documents(db, prepare_for_database(documents), prepare_for_database(chunks))
        finally:
            db.close()
        print("Stored RAG documents/chunks in Postgres with pgvector embeddings.")
    else:
        print("Skipped DB storage. Re-run with --store-db after Postgres is available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
