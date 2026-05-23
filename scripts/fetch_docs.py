import argparse
import base64
import json
import os
import time
from pathlib import Path
from typing import Any

import requests


DOC_ROOT_FILES = ("README.md", "README.rst", "CHANGELOG.md", "CONTRIBUTING.md", "CONTRIBUTING.rst")
DOC_DIRECTORIES = ("doc", "docs", "examples")
DOC_PATH_PREFIXES = ("README", "doc/", "docs/", "examples/", "CHANGELOG", "CONTRIBUTING")
DOC_EXTENSIONS = (".md", ".rst", ".txt")
PANDAS_FALLBACK_DOCS = (
    "README.md",
    "doc/source/getting_started/install.rst",
    "doc/source/getting_started/intro_tutorials/index.rst",
    "doc/source/user_guide/index.rst",
    "doc/source/user_guide/io.rst",
    "doc/source/user_guide/indexing.rst",
    "doc/source/user_guide/merging.rst",
    "doc/source/whatsnew/index.rst",
    "doc/source/development/contributing.rst",
)


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


def get_contents(owner: str, repo: str, path: str, branch: str) -> Any:
    for attempt in range(3):
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=github_headers(),
            params={"ref": branch},
            timeout=20,
        )
        if response.status_code == 404:
            return None
        if response.status_code in {502, 503, 504} and attempt < 2:
            time.sleep(1 + attempt)
            continue
        response.raise_for_status()
        return response.json()
    return None


def fetch_raw_file(owner: str, repo: str, path: str, branch: str) -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def list_directory_files(owner: str, repo: str, path: str, branch: str, limit: int = 80) -> list[str]:
    """List docs from targeted directories without walking the whole repo tree.

    Large repositories like pandas can time out on GitHub's recursive tree API.
    This focused traversal is enough for RAG docs and much more reliable.
    """

    payload = get_contents(owner, repo, path, branch)
    if not isinstance(payload, list):
        return []

    files: list[str] = []
    stack = [item for item in payload if item.get("type") in {"file", "dir"}]
    while stack and len(files) < limit:
        item = stack.pop(0)
        item_path = item["path"]
        if item.get("type") == "file" and should_keep(item_path):
            files.append(item_path)
        elif item.get("type") == "dir":
            child_payload = get_contents(owner, repo, item_path, branch)
            if isinstance(child_payload, list):
                stack.extend(child for child in child_payload if child.get("type") in {"file", "dir"})
    return files


def list_repo_files(owner: str, repo: str, branch: str) -> list[str]:
    paths: list[str] = []
    for root_file in DOC_ROOT_FILES:
        if get_contents(owner, repo, root_file, branch):
            paths.append(root_file)
    for directory in DOC_DIRECTORIES:
        paths.extend(list_directory_files(owner, repo, directory, branch))
    return sorted(set(paths))


def fetch_file(owner: str, repo: str, path: str, branch: str) -> str:
    try:
        payload = get_contents(owner, repo, path, branch)
        if isinstance(payload, dict) and payload.get("encoding") == "base64":
            return base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
        if isinstance(payload, dict):
            return payload.get("content", "")
    except requests.HTTPError:
        pass
    return fetch_raw_file(owner, repo, path, branch)


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

    if (args.owner, args.repo) == ("pandas-dev", "pandas"):
        # pandas is large enough that GitHub's tree/contents APIs often time
        # out during demos. These stable docs paths keep RAG ingestion reliable.
        kept_files = list(PANDAS_FALLBACK_DOCS)
    else:
        kept_files = [path for path in list_repo_files(args.owner, args.repo, args.branch) if should_keep(path)]
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
