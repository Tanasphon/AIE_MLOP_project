from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main


def make_image_bytes() -> bytes:
    image = Image.new("RGB", (32, 32), color=(255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def client(monkeypatch):
    async def fake_run_prediction(image_bytes: bytes, top_k: int) -> dict:
        return {
            "model": "apple/mobilevit-small",
            "runtime": "test",
            "top_k": top_k,
            "predictions": [{"label": "test-label", "score": 0.99}],
        }

    monkeypatch.setattr(main, "run_prediction", fake_run_prediction)
    return TestClient(main.app)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_endpoint_returns_json(client):
    response = client.post(
        "/predict",
        files={"file": ("sample.png", make_image_bytes(), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "apple/mobilevit-small"
    assert body["runtime"] == "test"
    assert body["predictions"][0]["label"] == "test-label"


def test_predict_rejects_non_image(client):
    response = client.post(
        "/predict",
        files={"file": ("bad.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
