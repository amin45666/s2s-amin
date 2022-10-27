import os
import uuid

import requests
from dependency import logging
from localStoragePy import localStoragePy

localStorage = localStoragePy("s2s", "json")
from dotenv import *

load_dotenv()
SEGMENTERAPI = os.environ.get("SEGMENTERAPI")
TRANSLATE_API_URL = os.environ.get("TRANSLATE_API_URL")
TRANSLATE_API_KEY = os.environ.get("TRANSLATE_API_KEY")
TRANSLATE_API_REGION = os.environ.get("TRANSLATE_API_REGION")
PARAPHRASE_API_URL = os.environ.get("PARAPHRASE_API_URL")
PARAPHRASE_API_AUTHORIZATION = os.environ.get("PARAPHRASE_API_AUTHORIZATION")


def translate(text, sourceLanguage, targetLanguages):
    """
    This calls the translation API (now AZURE)

    Parameters
    ----------
    text: text to be translated
    sourceLanguage: source language
    targetLanguages: list of targeted languages

    Returns
    -------
    translated segments

    """

    endpoint = TRANSLATE_API_URL
    subscription_key = TRANSLATE_API_KEY
    region = TRANSLATE_API_REGION

    sourceLanguage = "en"
    params = "&from=" + sourceLanguage
    for tl in targetLanguages:
        params = params + "&to=" + tl
    constructed_url = endpoint + params

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    body = [{"text": text}]

    request = requests.post(constructed_url, headers=headers, json=body)
    response = request.json()
    translations_list = response[0]["translations"]

    translations = {sourceLanguage: text}
    for translation_language in translations_list:
        translation = translation_language["text"]
        language = translation_language["to"]
        translations[language] = translation

    return translations


def segment(text, asr_status, sessionID, sourceLanguage):
    """
    This calls the segmenter API

    Parameters
    ----------
    text: original text
    asr_status: status of asr
    sessionID: sessionID of room
    sourceLanguage: source language

    Returns
    -------
    segments of original text
    """
    pload = {
        "text": text,
        "status": asr_status,
        "sessionID": sessionID,
        "sourceLanguage": sourceLanguage,
    }
    endpoint = f"{SEGMENTERAPI}/parse"

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        mysegment = ""
        try:
            mysegment = result[0]
        except:
            print("SEGMENTER did not return any segment")
        return mysegment
    else:
        result = {"error": response}
        return result


def paraphrase(text):
    """
    this calls the paraphrasing LM which is now a huggingface model hosted on their servers
    we may switch to other models. We may want to host it ourselves

    Parameters
    ----------
    text: original text

    Returns
    -------
    paraphrased text
    """
    API_URL = PARAPHRASE_API_URL
    headers = {"Authorization": PARAPHRASE_API_AUTHORIZATION}

    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    paraphrased_dic = response.json()
    paraphrased = paraphrased_dic[0]["generated_text"]

    return paraphrased


def initialize_segmenterAPI(sessionID):
    """
    this initializes a session of the Segmenter for this specific Session ID

    Parameters
    ----------
    sessionID: sessionID of room

    Returns
    -------
    'Session initiated' if session is successfully started

    OR

    'API initialization error' if session could not start successfully
    """
    pload = {
        "lang": "en",
        "min_one_noun": True,
        "remove_adv": False,
        "delay": 3,
        "sessionID": sessionID,
    }
    endpoint = f"{SEGMENTERAPI}/startSession"

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        initialize_cache_session()
        return "Session initiated"
    else:
        return "API initialization error"


def initialize_cache_session():
    """
    This initializes the cache session and sets the sessionId in local storage
    """
    session_settings = {
        "asr_callbacks": 0,
        "segment_nr": 0,
    }
    logging.info("Service")
    logging.warning("Service")
    logging.error("Service")
    localStorage.setItem("sessionId", session_settings)
