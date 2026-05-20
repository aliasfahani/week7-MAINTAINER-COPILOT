from typing import Any

import httpx

from app.config import get_settings


class ModelServerError(RuntimeError):
    pass


class ModelServerClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.model_server_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.model_client_timeout_seconds

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise ModelServerError(f"Could not reach model_server endpoint {path}") from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass
            raise ModelServerError(f"model_server {path} failed: {detail}")

        return response.json()

    def classify_issue(self, title: str, body: str) -> dict[str, Any]:
        return self._post("/classify", {"title": title, "body": body})

    def extract_entities(self, text: str) -> dict[str, Any]:
        return self._post("/ner", {"text": text})

    def summarize_text(self, text: str) -> dict[str, Any]:
        return self._post("/summarize", {"text": text})


def get_model_client() -> ModelServerClient:
    return ModelServerClient()
