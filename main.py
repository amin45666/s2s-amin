"""
Speech-to-Speech API.

Exposes methods to manage speech-to-speech cascading system.
"""
import ast
from typing import List

from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from localStoragePy import localStoragePy
from pydantic import BaseModel

from dependency import logging
from s2s.constants import USE_REWRITING, VOICE_SPEED_DEFAULT
from s2s.orchestrator import data_orchestrator
from s2s.service import *

localStorage = localStoragePy("s2s", "json")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class parseRequestData(BaseModel):
    """
    Request data model.

    It represents the request parameters.

    asr: string
        original text

    status: string
        status of asr

    room: string
        sessionID

    sourceLanguage: string
            source language

    targetLanguages: list
            list of target languages

    """

    asr: str
    status: str
    room: str
    sourceLanguage: str
    targetLanguages: list[str]


@app.get("/api/startSession/{sessionId}")
async def startSession(sessionId):
    """
    this initializes a session. Only session id is needed
    parameters such as languages can be passed here (instead of with transcription), but would require some storage
    a new session may spin a new Segmenter API -> Chandra

    Parameters
    ----------
    sessionID: sessionID of room

    Returns
    -------
    'Session initiated' if session is successfully started

    OR

    'API initialization error' if session could not start successfully
    """
    logging.info("Main")
    logging.warning("Main")
    logging.error("Main")
    return initialize_segmenterAPI(sessionId)


@app.get("/api/stopSession/{sessionId}")
async def stopSession(sessionId):
    """
    This flushes the cash and finish the session

    Parameters
    ----------
    sessionID: sessionID of room

    Returns
    -------
    'Session terminated'
    """
    localStorage.removeItem("sessionId")
    return "Session terminated"


@app.post("/api/parse")
def parse(data: parseRequestData):
    """
    this is the main call coming from the client
    the communication method will be changed according to the engineering team (probably sockets)

    Parameters
    ----------
    asr: original text
    status: status of asr
    room: sessionID
    sourceLanguage: source language
    targetLanguages: list of target languages

    Returns
    -------
    Translated segments
    """
    sourceLanguage = data.sourceLanguage
    targetLanguages = data.targetLanguages

    data_dict = vars(data)
    data_dict["rewriting"] = USE_REWRITING
    data_dict["voiceSpeed"] = VOICE_SPEED_DEFAULT
    print(data_dict)
    return data_orchestrator(data_dict, sourceLanguage, targetLanguages)


@app.websocket("/v1_0/meeting/{meeting_id}/source/{source_language}")
async def websocket_endpoint(
    websocket: WebSocket,
    meeting_id: str,
    source_language: str,
    targets: List[str] = Query(None),
):
    await websocket.accept()
    data = await websocket.receive_text()
    input_data = ast.literal_eval(data)
    data_dict = {
        "asr": input_data["text"],
        "status": input_data["status"],
        "room": meeting_id,
        "sourceLanguage": source_language,
        "targetLanguages": ["fr"],
        "rewriting": USE_REWRITING,
        "voiceSpeed": VOICE_SPEED_DEFAULT,
    }

    result = data_orchestrator(data_dict, source_language, targets)
    await websocket.send_text(f"{result}")
