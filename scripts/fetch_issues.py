import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch closed GitHub issues as JSONL.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", default="data/raw/issues.jsonl")
    parser.add_argument("--limit", type=int, default=500)
    return parser.parse_args()


def request_page(owner: str, repo: str, page: int, token: str | None) -> list[dict[str, Any]]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        headers=headers,
        params={
            "state": "closed",
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "asc",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def normalize_issue(issue: dict[str, Any]) -> dict[str, Any] | None:
    if "pull_request" in issue:
        return None

    return {
        "id": issue["id"],
        "number": issue["number"],
        "title": issue.get("title") or "",
        "body": issue.get("body") or "",
        "labels": [label.get("name", "") for label in issue.get("labels", [])],
        "state": issue.get("state"),
        "created_at": issue.get("created_at"),
        "closed_at": issue.get("closed_at"),
        "html_url": issue.get("html_url"),
        "comments": issue.get("comments", 0),
    }


def main() -> int:
    args = parse_args()
    token = os.getenv("GITHUB_TOKEN")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    page = 1
    with output.open("w", encoding="utf-8") as handle:
        while written < args.limit:
            issues = request_page(args.owner, args.repo, page, token)
            if not issues:
                break
            for issue in issues:
                normalized = normalize_issue(issue)
                if normalized is None:
                    continue
                handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                written += 1
                if written >= args.limit:
                    break
            page += 1

    print(f"Wrote {written} closed issues to {output}")
    if written == 0:
        print("No issues were written. Check repo labels/state or GitHub API access.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
