import pytest
from fastapi.testclient import TestClient
from main import app
from s2s.service import (
    segment,
    initialize_segmenterAPI,
    translate,
    paraphrase
)

client = TestClient(app)



def test_segment():
    text = "Hey, I am from Pakistan. It is a really beautiful country."
    asr_status = "temporary"
    sessionID = "123"
    sourceLanguage = "en"
    result = segment(text, asr_status, sessionID, sourceLanguage)
    if type(result) is str:
        assert True
    else:
        assert False

def test_initialize_segmenterAPI():
    sessionID = "123"
    result = initialize_segmenterAPI(sessionID)
    if result == "Session initiated":
        assert True

def test_translate():
    text = "I am from Pakistan"
    sourceLanguage = "en"
    targetLanguages = ["fr"]
    result = translate(text, sourceLanguage, targetLanguages)

    if "en" and "fr" in result:
        assert True
    else:
        assert False

def test_paraphrase():
    text = "I am from Pakistan"
    result = paraphrase(text)

    if type(result) is str:
        assert True
    else:
        assert False