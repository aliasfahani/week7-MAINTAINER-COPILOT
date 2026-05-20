import httpx
import pytest

from app.infra.model_client import ModelServerClient, ModelServerError


def test_model_client_success(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return httpx.Response(
            200,
            json={
                "label": "bug",
                "confidence": 0.8,
                "scores": {"bug": 0.8},
                "model_version": "test",
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = ModelServerClient(base_url="http://model-server", timeout_seconds=1)
    assert client.classify_issue("Crash", "Fails")["label"] == "bug"


def test_model_client_failure_is_clean(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return httpx.Response(503, json={"detail": "model unavailable"})

    monkeypatch.setattr(httpx, "post", fake_post)
    client = ModelServerClient(base_url="http://model-server", timeout_seconds=1)
    with pytest.raises(ModelServerError, match="model unavailable"):
        client.classify_issue("Crash", "Fails")
