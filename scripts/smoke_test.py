import sys

import requests


def check(url: str) -> None:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    print(f"{url} -> {response.json()}")


def main() -> int:
    check("http://localhost:8000/health")
    check("http://localhost:8001/health")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
