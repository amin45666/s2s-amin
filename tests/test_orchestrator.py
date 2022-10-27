import pytest
from fastapi.testclient import TestClient
from main import app
from s2s.orchestrator import data_orchestrator

client = TestClient(app)


def test_data_orchestrator():
    data_dict = {
        "asr": "Hey, I am from Pakistan. Where are you from?",
        "status": "temporary",
        "room": "123",
        "sourceLanguage": "en",
        "targetLanguages": ["fr", "es"],
        "rewriting": False,
        "voiceSpeed": 15,
    }
    payload_rcvd = data_orchestrator(data_dict, "en", ["fr"])
    assert payload_rcvd["status"]
