import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch closed GitHub issues as JSONL.")
    parser.add_argument("--owner", default="pandas-dev")
    parser.add_argument("--repo", default="pandas")
    parser.add_argument("--output", default="data/raw/issues.jsonl")
    parser.add_argument("--limit", type=int, default=2000)
    parser.add_argument(
        "--labels",
        default="bug,enhancement,Docs,Usage Question",
        help="Comma-separated labels to fetch separately. Use an empty string to fetch all closed issues.",
    )
    parser.add_argument("--per-label-limit", type=int, default=500)
    return parser.parse_args()


def request_page(owner: str, repo: str, page: int, token: str | None, label: str | None = None) -> list[dict[str, Any]]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "state": "closed",
        "per_page": 100,
        "page": page,
        "sort": "created",
        "direction": "asc",
    }
    if label:
        params["labels"] = label

    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        headers=headers,
        params=params,
        timeout=20,
    )
    if response.status_code == 422 and page > 10:
        # GitHub can reject very deep issue pagination. For classifier data we
        # fetch per label, so stopping at this cap is better than failing after
        # writing useful examples.
        return []
    response.raise_for_status()
    return response.json()


def fetch_issues(owner: str, repo: str, token: str | None, limit: int, label: str | None = None) -> list[dict[str, Any]]:
    rows = []
    page = 1
    while len(rows) < limit:
        issues = request_page(owner, repo, page, token, label=label)
        if not issues:
            break
        for issue in issues:
            normalized = normalize_issue(issue)
            if normalized is None:
                continue
            rows.append(normalized)
            if len(rows) >= limit:
                break
        page += 1
    return rows


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

    requested_labels = [label.strip() for label in args.labels.split(",") if label.strip()]
    by_id: dict[int, dict[str, Any]] = {}
    if requested_labels:
        for label in requested_labels:
            rows = fetch_issues(args.owner, args.repo, token, args.per_label_limit, label=label)
            print(f"Fetched {len(rows)} closed non-PR issues with label {label!r}")
            for row in rows:
                by_id[row["id"]] = row
            if len(by_id) >= args.limit:
                break
    else:
        for row in fetch_issues(args.owner, args.repo, token, args.limit):
            by_id[row["id"]] = row

    rows = sorted(by_id.values(), key=lambda row: row.get("created_at") or "")
    rows = rows[: args.limit]

    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} closed issues to {output}")
    if not rows:
        print("No issues were written. Check repo labels/state or GitHub API access.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
