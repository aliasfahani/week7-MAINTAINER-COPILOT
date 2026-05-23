from fastapi.testclient import TestClient

from model_server.main import app


def test_model_server_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "model_server"}


def test_model_server_classify_missing_model_is_controlled() -> None:
    client = TestClient(app)
    response = client.post(
        "/classify",
        json={"title": "Login fails in production", "body": "JWT token is invalid after deploy"},
    )
    assert response.status_code in {200, 503}
    if response.status_code == 200:
        body = response.json()
        assert set(body) == {"label", "confidence", "scores", "model_version"}
    else:
        assert "Classifier artifact" in response.json()["detail"]


def test_model_server_ner_extracts_code_entities() -> None:
    client = TestClient(app)
    response = client.post(
        "/ner",
        json={"text": "After upgrading to v2.1.0, auth.py throws TypeError on Python 3.11."},
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert {"text": "auth.py", "type": "file"} in entities
    assert {"text": "TypeError", "type": "error"} in entities


def test_model_server_ner_extracts_pandas_parameters() -> None:
    client = TestClient(app)
    response = client.post(
        "/ner",
        json={"text": "Please add a clearer read_csv example showing parse_dates with multiple columns."},
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(item["text"].lower() == "parse_dates" for item in entities)
    assert any(item["text"].lower() == "read_csv" for item in entities)


def test_model_server_summarize_returns_summary_and_method() -> None:
    client = TestClient(app)
    response = client.post(
        "/summarize",
        json={"text": "First sentence. Second sentence. Third sentence. Fourth sentence."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]
    assert body["method"] == "simple_extractive"


def test_model_server_summarize_long_text_uses_safe_fallback_by_default() -> None:
    client = TestClient(app)
    text = " ".join(
        [
            "I had to search through several examples before understanding the correct format.",
            "It would be helpful to add a clearer example showing parse_dates with multiple columns.",
        ]
        * 8
    )
    response = client.post("/summarize", json={"text": text})
    assert response.status_code == 200
    body = response.json()
    assert "parse_dates" in body["summary"]
    assert body["method"] == "simple_extractive"
