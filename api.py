import os
import uuid

import requests
from dotenv import *

load_dotenv()
SEGMENTERAPI = os.environ.get("SEGMENTERAPI")
TRANSLATE_API_URL = os.environ.get("TRANSLATE_API_URL")
TRANSLATE_API_KEY = os.environ.get("TRANSLATE_API_KEY")
TRANSLATE_API_REGION = os.environ.get("TRANSLATE_API_REGION")
PARAPHRASE_API_URL = os.environ.get("PARAPHRASE_API_URL")
PARAPHRASE_API_AUTHORIZATION = os.environ.get("PARAPHRASE_API_AUTHORIZATION")


def translate(text, tl_list):
    """
    this calls the translation API (now AZURE)
    """
    print("Calling Translation API")

    # Azure endpoint
    endpoint = TRANSLATE_API_URL
    subscription_key = TRANSLATE_API_KEY
    region = TRANSLATE_API_REGION

    # constructing language parameters for call
    sl = "en"
    params = "&from=" + sl
    for tl in tl_list:
        params = params + "&to=" + tl
    constructed_url = endpoint + params

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    # You can pass more than one object in body
    body = [{"text": text}]

    request = requests.post(constructed_url, headers=headers, json=body)
    response = request.json()
    translations_list = response[0]["translations"]

    # create response data structure
    translations = {sl: text}
    for translation_language in translations_list:
        translation = translation_language["text"]
        language = translation_language["to"]
        translations[language] = translation

    return translations


def segment(text, asr_status, sessionID):
    """
    this calls the Segmenter
    """
    print("Calling Segmentation API")

    # constructing parameters for call. tl should contain more languages
    pload = {"text": text, "status": asr_status, "sessionID": sessionID}
    endpoint = SEGMENTERAPI + "/parse"

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


def paraphrase(text, sl):
    """
    this calls the paraphrasing LM which is now a huggingface model hosted on their servers
    we may switch to other models. We may want to host it ourselves
    """
    print("Calling Paraphrasing API")
    API_URL = PARAPHRASE_API_URL
    headers = {"Authorization": PARAPHRASE_API_AUTHORIZATION}

    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    paraphrased_dic = response.json()
    paraphrased = paraphrased_dic[0]["generated_text"]

    return paraphrased


def initialize_segmenterAPI(sessionID):
    """
    this inizializes a session of the Segmenter for this specific Session ID
    """
    print(PARAPHRASE_API_AUTHORIZATION)
    # we initialize the session with some parameters. The most important is the Session ID
    pload = {
        "lang": "en",
        "min_one_noun": True,
        "remove_adv": False,
        "delay": 3,
        "sessionID": sessionID,
    }
    endpoint = SEGMENTERAPI + "/startSession"

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        print("Initializing API: " + str(result))
        return result
    else:
        print("Error initializing of API: " + str(response))
        result = "API initialisation error"
