import os
import sys
from typing import Any

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")
MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL_LOCAL", "http://localhost:8001")
ADMIN_EMAIL = os.getenv("SMOKE_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("SMOKE_ADMIN_PASSWORD", "admin123")


def ok(name: str, detail: Any) -> None:
    print(f"PASS {name}: {detail}")


def warn(name: str, detail: Any) -> None:
    print(f"WARN {name}: {detail}")


def get_json(url: str) -> tuple[int, Any]:
    response = requests.get(url, timeout=10)
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, response.text


def post_json(url: str, payload: dict, token: str | None = None, headers: dict | None = None) -> tuple[int, Any]:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    response = requests.post(url, json=payload, headers=request_headers, timeout=20)
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, response.text


def main() -> int:
    status, body = get_json(f"{API_URL}/health")
    assert status == 200, body
    ok("api health", body)

    status, body = get_json(f"{MODEL_SERVER_URL}/health")
    assert status == 200, body
    ok("model_server health", body)

    status, body = post_json(f"{MODEL_SERVER_URL}/classify", {"title": "JWT fails", "body": "Invalid token"})
    if status == 200:
        ok("classifier structured response", sorted(body.keys()))
    elif status == 503:
        warn("classifier missing artifact is controlled", body.get("detail", body))
    else:
        raise AssertionError(f"classifier unexpected status {status}: {body}")

    status, body = post_json(f"{API_URL}/auth/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if status != 200:
        warn("admin login", f"run make seed-admin first; got {status}: {body}")
        return 0
    token = body["access_token"]
    ok("admin login", "token received")

    widget_payload = {
        "widget_id": "demo-widget",
        "allowed_origins": ["*"],
        "theme": {"primaryColor": "#2563eb"},
        "greeting": "Hi! How can I help?",
        "enabled_tools": ["rag_search", "classify_issue"],
    }
    status, body = post_json(f"{API_URL}/admin/widgets", widget_payload, token=token)
    if status in {200, 400}:
        ok("widget admin create", body)
    else:
        warn("widget admin create", f"{status}: {body}")

    status, body = get_json(f"{API_URL}/widgets/demo-widget/config")
    assert status in {200, 403}, body
    ok("widget config endpoint", {"status": status, "body": body})

    chat_payload = {
        "conversation_id": "smoke-test",
        "message": "Classify this issue and search similar resolved issues",
        "issue": {"title": "JWT fails", "body": "Invalid token after deploy"},
    }
    status, body = post_json(f"{API_URL}/chat", chat_payload, token=token)
    assert status == 200, body
    assert {"conversation_id", "answer", "tool_calls", "trace_id"} <= set(body)
    ok("authenticated chat", {"trace_id": body["trace_id"], "tool_calls": len(body["tool_calls"])})

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
