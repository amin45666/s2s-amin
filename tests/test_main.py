import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_session():
    response = client.get("/api/startSession/123")
    assert response.status_code == 200
    assert response.text.replace('"', "") == "Session initiated"


def test_stop_session():
    response = client.get("/api/startSession/123")
    response = client.get("/api/stopSession/123")
    assert response.status_code == 200
    assert response.text.replace('"', "") == "Session terminated"


def test_parse():
    response = client.get("/api/startSession/123")
    payload = {
        "asr": "How are you, I am from pakistan",
        "status": "temporary",
        "room": "123",
        "sourceLanguage": "en",
        "targetLanguages": ["fr", "es"],
    }
    response_parse = client.post("/api/parse", json=payload)
    assert response_parse.status_code == 200
