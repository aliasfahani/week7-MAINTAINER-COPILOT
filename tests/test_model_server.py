from fastapi.testclient import TestClient

from model_server.main import app


def test_model_server_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "model_server"}


def test_model_server_classify_stub() -> None:
    client = TestClient(app)
    response = client.post("/classify", json={"text": "The app crashes on startup"})
    assert response.status_code == 200
    assert response.json()["label"] == "bug"
