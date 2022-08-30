import json
import os
import flask
import requests
from flask import (Flask, Response, abort, flash, jsonify, make_response, redirect, render_template, request, session, url_for)
import uuid
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from werkzeug.utils import secure_filename

app = flask.Flask(__name__)
app.secret_key = 'caehvae89m'
globalTargetLanguage = "eu-ES"
socketio = SocketIO(app)

CORS(app)

###############################################
# WELCOME
###############################################
@app.route('/')
def login():
    #return render_template('login.html')
    return render_template('sender.html', sessionId="ciao")

@app.route('/sender', methods = ['GET', 'POST'])
def open_page_asr():
    return render_template('sender.html', sessionId="ciao")

@app.route('/receiver', methods = ['GET', 'POST'])
def open_page_receiver():
    return render_template('receiver.html', sessionId="ciao")

###################
# AZURE ASR
###################
#client ASR asks token
@app.route('/api/azureToken')
def azureToken():
    headers = {'content-type': 'application/x-www-form-urlencoded', "Ocp-Apim-Subscription-Key": "6af6abea507a4e09ae379b22e79ef25a"}
    url = 'https://eastus.api.cognitive.microsoft.com/sts/v1.0/issuetoken'
    data = ''
    params = {}
    response = requests.post(url, params=params, data=data, headers=headers)
    response.status_code
    if (response.status_code == 200):
        return response.text
    return 'Error'  
    
###############################################
# SOCKETS
###############################################

@socketio.on("message")
def handleMessage(data):
    text_translation  = data['translation']
    targetLanguageAbb = data['targetLanguage']
    room              = data['room']
    emit("caption", {'translation':text_translation, 'targetLanguageAbb':targetLanguageAbb}, broadcast=True, room=room)
    
@socketio.on("mt")
def handleMessage(data):
    text_translation  = data['data']
    room = data['room']
    counter = data['counter']
    flag = data['flag']
    targetLanguage = data["targetLanguage"]
    emit("machineTranslation", {"text_translation":text_translation, "counter":counter, "flag":flag, "targetLanguage":targetLanguage}, broadcast=True, room=room)

@socketio.on("languageEmitter")
def on_join(data):
    global globalTargetLanguage
    targetLanguage = data["targetLanguage"]
    room = data["room"]
    globalTargetLanguage = targetLanguage
    print(targetLanguage)
    emit("caption", {"msg":"language changed occur", "tl":targetLanguage}, room=room)

###############################################
# JOINING/LEAVING SESSIONS
###############################################
@socketio.on("join")
def on_join(data):
    global globalTargetLanguage
    user = data["user"]
    room = data["room"]
    targetLanguage = data["targetLanguage"]
    if targetLanguage == "":
        targetLanguage = globalTargetLanguage
    else:
        globalTargetLanguage = targetLanguage
    join_room(room)
    emit("caption", {"msg":f"User {user} joint event {room},", "tl":targetLanguage}, room=room)

@socketio.on('leave')
def on_left(data):
    user = data["user"]
    room = data["room"]
    leave_room(room)
    
if __name__ == "__main__":
    socketio.run(app, debug=True)
