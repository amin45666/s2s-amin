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

from api import *
from constants import TLS_LIST
from decorators import roles_required
from helpers import id_generator, login_authentication, print_changelog
from orchestrator import data_orchestrator

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")

app = flask.Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)

# this R&D switch is to be deleted
# switch to make log of session for the moment temporary until this is not finalized
CK_log_session = True


""" 
Instantiate the cache
This is the volatile place whre we store Session dependent informations updated at any callback from ASR
"""

cache = Cache()
cache.init_app(app=app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 36000})


###############################################
# SERVICE API TO CALL FOR real-time S2S
###############################################

@app.route("/api/parse", methods=["POST"])
def parse():
    """
    this is the main call coming from the client
    the communication method will be changed according to the engineering team (probably sockets)
    """
    data = request.get_json()

    # adding some defaults value to the parameters send by the client
    # these parameters are still object of R&D
    data["paraphraseFeature"] = True
    data["voiceSpeed"] = 10

    response = data_orchestrator(data, cache, CK_log_session)
    json_object = json.dumps(response, indent=4)

    # the service responds with a JSON package containing the translation(s) and parameters for the text-to-speech
    return json_object

@app.route("/api/startSession/<sessionId>")
def startSession(sessionId):

    # this initiate a session of S2S
    # consumer needs to pass a unique ID, source language and target language(s)

    # changin this to a POST call to accept parameters 
    # move to -> , methods=['POST']
    # data = request.get_json()
    # languages = data['languages'] # to be done
    # print("Session for languages: " + languages)

    # initiate a new session of API
    initialize_segmenterAPI(sessionId)
    session_settings = {
        "asr_callbacks": 0,
        "asr_segments": 0,
    }
    cache.set(sessionId, session_settings)

    return "Session initiated"


@app.route("/api/stopSession/<sessionId>")
def stopSession(sessionId):

    # this is still to be done
    # this should flash the cash for this session
    print("Terminating session: " + str(sessionId))

    return "Session terminated"

###############################################
# END SERVICE API
###############################################



##############################################################################################
# THIS ARE THE ROUTS FOR THE USER FACING POC - TO BE DISCARDED FOR THE SERVICE API
# we should probably move it in a separate .py since this is used only temporary to run APP
##############################################################################################
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
        "asr_callbacks": 0,
        "asr_segments": 0,
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
        "asr_callbacks": 0,
        "asr_segments": 0,
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

    changelog = print_changelog()

    return Response(json.dumps(changelog), mimetype="application/json")


# this is the orchestrator which is continuously called with the transcription and metadata
@socketio.on("message")
def receive_socket(data):
    sessionID = data["room"]

    response = data_orchestrator(data, cache, CK_log_session)

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
# END OF USER FACING POC
###############################################

if __name__ == "__main__":
    socketio.run(app, debug=True)
