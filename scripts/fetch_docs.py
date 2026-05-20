import argparse
import base64
import json
import os
from pathlib import Path
from typing import Any

import requests


DOC_PATH_PREFIXES = ("README", "docs/", "examples/", "CHANGELOG", "CONTRIBUTING")
DOC_EXTENSIONS = (".md", ".rst", ".txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch GitHub documentation files for RAG.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--raw-dir", default="data/raw/docs")
    parser.add_argument("--output", default="data/processed/rag_docs.jsonl")
    return parser.parse_args()


def github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    return headers


def should_keep(path: str) -> bool:
    upper_path = path.upper()
    return path.endswith(DOC_EXTENSIONS) and any(
        path.startswith(prefix) or upper_path.startswith(prefix) for prefix in DOC_PATH_PREFIXES
    )


def list_repo_files(owner: str, repo: str, branch: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}",
        headers=github_headers(),
        params={"recursive": "1"},
        timeout=20,
    )
    response.raise_for_status()
    return [item for item in response.json().get("tree", []) if item.get("type") == "blob"]


def fetch_file(owner: str, repo: str, path: str, branch: str) -> str:
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        headers=github_headers(),
        params={"ref": branch},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("encoding") == "base64":
        return base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
    return payload.get("content", "")


def title_from_path(path: str) -> str:
    name = Path(path).name
    return name.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title()


def main() -> int:
    args = parse_args()
    repo_name = f"{args.owner}/{args.repo}"
    raw_dir = Path(args.raw_dir)
    output = Path(args.output)
    raw_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    kept_files = [item["path"] for item in list_repo_files(args.owner, args.repo, args.branch) if should_keep(item["path"])]
    rows = []
    for path in kept_files:
        text = fetch_file(args.owner, args.repo, path, args.branch)
        raw_path = raw_dir / path
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(text, encoding="utf-8")

        rows.append(
            {
                "source_type": "docs",
                "source_id": f"docs/{path}",
                "title": title_from_path(path),
                "url": f"https://github.com/{repo_name}/blob/{args.branch}/{path}",
                "text": text,
                "metadata": {"path": path, "repo": repo_name, "branch": args.branch},
            }
        )

    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Fetched {len(rows)} documentation files into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
