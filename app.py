import json
import os

import flask
from dotenv import *
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_caching import Cache
from flask_socketio import SocketIO, emit, join_room, leave_room

# from api import initialize_segmenterAPI, paraphrase, segment, translate
from api import *
from constants import SL, TLS_LIST, VOICE_SPEED_DEFAULT
from decorators import roles_required
from helpers import id_generator, login_authentication
from orchestrator import log_duration_TL, log_timestamp_SL

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")

app = flask.Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)

# switch to make log of session for the moment temporary until this is not finalized
CK_log_session = True

# the real APP should send an initialisation payload with sl and list of tl
# TO DO: mimic here a json payload


# Instantiate the cache. This is the place to store Session dependent information
# We save now the progressive number of ASR callback to log data
cache = Cache()
cache.init_app(app=app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 36000})

# AMIN move everything until END UI to poc.py
###############################################
# UI
###############################################
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_data = request.form.to_dict()
        email = form_data.get("email", None)
        password = form_data.get("password", None)
        if email and password:
            app.logger.info(f"User email: {email}")
            response = login_authentication(email, password)
            if response["status"] in ["user unkown", "not allowed"]:
                flash("Invalid username or password")
                return redirect(url_for("login"))
            else:
                session.clear()
                session["role"] = response["role"]
                return redirect(url_for(session["role"]))
        else:
            flash("Empty username or password")
            return redirect(url_for("login"))
    return render_template("login.html", title="Login")


# this is the default SENDER view. Opening this page generates a session ID, initializes the Segmenter API with the session ID and creates the view
@app.route("/sender", methods=["GET", "POST"])
@roles_required("sender")
def sender():

    # create a random session ID
    sessionId = id_generator()

    # initiate a new session of API
    initialize_segmenterAPI(sessionId)
    session_settings = {
        "asr_callbacks" : 0,
        "asr_segments" : 0,
    }
    cache.set(sessionId, session_settings)

    return render_template("sender.html", sessionId=sessionId, languages=TLS_LIST)


# this is the advanced SENDER view (with testing options). Opening this page generates a session ID, initializes the Segmenter API with the session ID and creates the view
@app.route("/consolle", methods=["GET", "POST"])
@roles_required(["sender"])
def consolle():

    # create a random session ID
    sessionId = id_generator()

    # initiate a new session of API
    initialize_segmenterAPI(sessionId)
    session_settings = {
        "asr_callbacks" : 0,
        "asr_segments" : 0,
    }
    cache.set(sessionId, session_settings)

    return render_template("consolle.html", sessionId=sessionId, languages=TLS_LIST)


# this is the receiver view which will receive the translation and the interpretation
@app.route("/receiver", methods=["GET", "POST"])
def receiver():

    return render_template("receiver.html", languages=TLS_LIST)


# this route returns info on the version log
@app.route("/info")
def info():
    changelog = [
        {"minor version": 0, "details": "initial POC commit", "date": "2022-09-14"},
        {"minor version": 1, "details": "adds version changelog", "date": "2022-09-14"},
        {"minor version": 2, "details": "adds multichannel", "date": "2022-09-14"},
        {
            "minor version": 3,
            "details": "improves UI for Sender/Receiver",
            "date": "2022-09-15",
        },
        {
            "minor version": 4,
            "details": "adds automatic scrolling in Sender table",
            "date": "2022-09-15",
        },
        {
            "minor version": 5,
            "details": "adds timestamp of segment processing",
            "date": "2022-09-15",
        },
        {"minor version": 6, "details": "adds logfile", "date": "2022-09-15"},
        {
            "minor version": 7,
            "details": "adds parameter to reduce calls of API",
            "date": "2022-09-16",
        },
        {
            "minor version": 8,
            "details": "adds feature to improve accuracy with list of terms",
            "date": "2022-09-17",
        },
        {
            "minor version": 9,
            "details": "improves SENDER UI; fix sampling frequency logic",
            "date": "2022-09-19",
        },
        {"minor version": 10, "details": "improves Receiver UI;", "date": "2022-09-19"},
        {
            "minor version": 11,
            "details": "improves sampling frequency logic from APP",
            "date": "2022-09-20",
        },
        {
            "minor version": 12,
            "details": "improves UI Sender; make logging optional (hard coded switch)",
            "date": "2022-09-21",
        },
        {
            "minor version": 13,
            "details": "adds optional AI rephrasing for longer sentences >20 tokens",
            "date": "2022-09-21",
        },
        {
            "minor version": 14,
            "details": "adds API initialisation call with sessionID",
            "date": "2022-09-21",
        },
        {
            "minor version": 15,
            "details": "minor improvements to Receiver UI",
            "date": "2022-09-22",
        },
        {
            "minor version": 16,
            "details": "adds multilingual support",
            "date": "2022-09-22",
        },
        {
            "minor version": 17,
            "details": "adding new timer logic",
            "date": "2022-09-29",
        },
        {
            "minor version": 18,
            "details": "adding controller of voice speed in SENDER",
            "date": "2022-10-02",
        },
        {
            "minor version": 19,
            "details": "new control of session initialisation for segmentation API",
            "date": "2022-10-05",
        },
        {
            "minor version": 20,
            "details": "improved responsivness of RECEIVER",
            "date": "2022-10-06",
        },
        {
            "minor version": 21,
            "details": "adding simple SENDER page with standard settings",
            "date": "2022-10-12",
        },
        {
            "minor version": 22,
            "details": "adding simple login page",
            "date": "2022-10-13",
        },
        {"minor version": 23, "details": "cleaning code", "date": "2022-10-17"},
        {
            "minor version": 24,
            "details": "fix stop translation after 10 segments",
            "date": "2022-10-18",
        },
    ]

    return Response(json.dumps(changelog), mimetype="application/json")

# this is the orchestrator which is continuously called with the transcription and metadata
@socketio.on("message")
def receive_socket(data):
    sessionID = data["room"]  

    response = orchestrator(data)
    
    # emitting payload to client for TTS
    print("Emitting payload to receiver")
    emit(
        "caption",
        response,
        broadcast=True,
        room=sessionID,
    )

@socketio.on("join")
def on_join(data):
    user = data["user"]
    sessionID = data["room"]
    print(f"client {user} wants to join: {sessionID}")
    join_room(sessionID)
    emit("caption", f"User {user} joint event {sessionID},", room=sessionID)


@socketio.on("leave")
def on_left(data):
    user = data["user"]
    sessionID = data["room"]
    print(f"client {user} wants to leave: {sessionID}")
    leave_room(sessionID)

    emit("caption", f"User {user} left event {sessionID},", room=sessionID)

###############################################
# END UI
###############################################

# AMIN please move until END SERVICE to service.py
###############################################
# SERVICE
###############################################
@app.route('/api/startSession/<sessionId>')
def startSession(sessionId):

    # move to -> , methods=['POST']
    #data = request.get_json()  
    #languages = data['languages'] # to be done
    #print("Session for languages: " + languages)

    # initiate a new session of API
    initialize_segmenterAPI(sessionId)
    session_settings = {
        "asr_callbacks" : 0,
        "asr_segments" : 0,
    }
    cache.set(sessionId, session_settings)

    return "Session initiated"

@app.route('/api/stopSession/<sessionId>')
def stopSession(sessionId):

    #to be done
    print("Terminating session: " + str(sessionId))

    return "Session terminated"

#the following method to call the API will be changed according to Engineering team (some sockets)
@app.route('/api/parse', methods=['POST'])
def parse():

    data = request.get_json()

    #setting some defaults
    data["paraphraseFeature"] = True
    data["voiceSpeed"] = 10

    response = orchestrator(data)
    json_object = json.dumps(response, indent = 4) 
    return json_object

###############################################
# END SERVICE
###############################################


# AMIN please move the following def to orchestrator.py (if namespace is not okay, change what is needed)
def orchestrator(data):
    # the orchestrator is receiving the transcription stream and a series of metadata associated to a session
    asr_text = data["asr"]  # transcription
    asr_status = data["status"]  # this is the status of ASR (temporary/final/silence)
    sessionID = data["room"]  # session ID
    paraphraseFeature = data["paraphraseFeature"]  # enable paraphrasing feature
    voiceSpeed = data[
        "voiceSpeed"
    ]  # force a voice speed (default = 1, otherwise changed by orchestrator)
    ck_lang = data[
        "ck_lang"
    ]  # use only 1 target language or many - should be changed with a list of required languages

    # getting the progressive callback number for this session
    session_settings = cache.get(sessionID)
    asr_callbacks = session_settings["asr_callbacks"]
    asr_segments = session_settings["asr_segments"]

    print(
        "\nOrchestrator has been called for session: "
        + str(sessionID)
        + " and callback number: "
        + str(asr_callbacks)
    )
    print(
        f"Data received from SENDER:\n\ttext: '{asr_text}'\n\tstatus: '{asr_status}'\n\tsession: '{sessionID}'\n\tspeed: '{voiceSpeed}'"
    )

    # SETTING DEFAULTS IF NO WALUES ARE PASSED
    # TO DO: there must be a better way to set defaults
    if voiceSpeed == "":
        voiceSpeed = VOICE_SPEED_DEFAULT  # default value
        print("No voice speed was passed, setting to default: " + str(voiceSpeed))

    # send asr to segmenter and see if there is a response
    mysegment = segment(asr_text, asr_status, sessionID)

    # recording timestamp when SL has been received
    if CK_log_session:
        log_timestamp_SL(asr_callbacks)

    # proceed only if the Segmentator has returned a segment
    if mysegment:
        print("DATA received from SEGMENTER:\n\ttext: " + mysegment)

        paraphrasedAPPLIED = (
            ""  # this variable keeps track if the paraphrasing has been applied or not
        )

        # deciding if a segment needs to be paraphrased (typically to improve readibility and make it shorter)
        if paraphraseFeature:
            countOfWords = len(mysegment.split())
            # we paraphrase only long segments for now. This parameter should be moved to Orchestrator default settings
            if countOfWords > 20:
                mysegment = paraphrase(mysegment, SL)
                print("Paraphrase returned: ")
                print(mysegment)
                paraphrasedAPPLIED = "TRUE"

        # deciding in which languages to translate. For semplicity reasons, it is now either ES or ALL supported languages
        # rewrite passing a list of languages
        tls_list_send = [""]
        if ck_lang != "all":
            tls_list_send = ["es"]
        else:
            tls_list_send = TLS_LIST

        # translating the segment in target languages
        mytranslations = translate(mysegment, tls_list_send)

        # estimate time of TTS based on language and speed of voice
        # create session matrix with segment Nr + Duration SL + estimation in TL

        print("Translations returned: ")
        print(mytranslations)

        if CK_log_session:
            log_duration_TL(asr_callbacks, mytranslations, voiceSpeed)

        # updating number of callback for this session
        asr_callbacks = asr_callbacks + 1
        asr_segments = asr_segments + 1
        session_settings = {
            "asr_callbacks" : asr_callbacks,
            "asr_segments" : asr_segments,
        }
        cache.set(sessionID, session_settings)

        mytranslations_json = json.dumps(mytranslations)

        payload =   {
                "asr": asr_text,
                "segment": mytranslations_json,
                "paraphraseFeature": paraphrasedAPPLIED,
                "voiceSpeed": voiceSpeed,
            }

        return payload

    else:

        asr_callbacks = asr_callbacks + 1
        session_settings = {
            "asr_callbacks" : asr_callbacks,
            "asr_segments" : asr_segments,
        }

        


if __name__ == "__main__":
    socketio.run(app, debug=True)
