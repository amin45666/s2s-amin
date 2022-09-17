import flask
from flask import Flask, flash, Response, redirect, send_file, url_for, request, session, abort, render_template, make_response, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import os
import json
import requests, uuid
import random
from datetime import datetime

app = flask.Flask(__name__)
app.secret_key = 'jhgwjhdgwjhd3d'
socketio = SocketIO(app)

logfile = open('log/logAPP.txt', 'a')
logfile.write("logline\n")
###############################################
# WELCOME
###############################################

@app.route("/", methods=["GET", "POST"])
def open_page_asr():
    
    print('OPENING SESSION')
    asr            = 'ok' #show toggle button to show real-time transcription     
    url_client     = '' 
    client         = 1
    langs_flat     = 'Spanish'
    languages_list = langs_flat.split(':')

    sessionId = random.randint(1000,9999)


    return render_template('asr.html', sessionId=sessionId, asr=asr, client=client, languages=languages_list, url_client=url_client)

@app.route("/receiver", methods=["GET", "POST"])
def open_page_receiver():

    langs_flat     = 'Spanish'

    languages_list = langs_flat.split(':')
    return render_template("receiver.html", languages=languages_list)

@app.route('/info')
def info():
    changelog = [
        {'minor version': 0, 'details': 'initial POC commit', 'date': '2022-09-14'},
        {'minor version': 1, 'details': 'adding version changelog', 'date': '2022-09-14'},
        {'minor version': 2, 'details': 'adding multichannel', 'date': '2022-09-14'},
        {'minor version': 3, 'details': 'improved UI for Sender/Receiver', 'date': '2022-09-15'},
        {'minor version': 4, 'details': 'added automatic scrolling in Sender table', 'date': '2022-09-15'},
        {'minor version': 5, 'details': 'added timestamp of segment processing', 'date': '2022-09-15'},
        {'minor version': 6, 'details': 'added logfile', 'date': '2022-09-15'},
        {'minor version': 7, 'details': 'added parameter to reduce calls of API', 'date': '2022-09-16'},
        {'minor version': 8, 'details': 'added feature to improve accuracy with list of terms', 'date': '2022-09-17'},

    ]

    return Response(json.dumps(changelog),  mimetype='application/json')

#########################
#  APIs 
#########################
@app.route('/api/log/<filename>')
def doc_file(filename):

    file = os.path.join('log', filename)
    with open(file, 'r') as logfile:
        log = logfile.read().replace('\n', '<br>')
        return log

###############################################
# LIVE
###############################################

@socketio.on("message")
def handleMessage(data):

    asr = data['asr']
    final = data['final']
    room = data['room']

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    logfile.write("\n")
    logline = str(current_time) + '\t' + 'ASR\t' + str(asr)
    logfile.write(logline)
    logfile.write("\n")

    print(f"\nProcessing '{asr}' with state '{final}' for Session '{room}' and time '{current_time}'")

    #languages should be dynamic, and tl more than one
    sl = 'en'
    tl = 'es' # tl should be list containing more languages

    #reducing number of time the API is called
    number_of_words = len(asr.split())
    print(number_of_words)

    #send asr to segmenter and see if there is a response
    segment_sl = segment(asr, final)

    if segment_sl:
        print("API returned segment: ")
        print(segment_sl)

        #translate segment to targ languages (will be more than one tl)
        translation = translate(segment_sl[0], tl)

        #creating payload. This will need to be dynamic
        segment_payload = {
            sl : segment_sl,
            tl : translation
        }
        segment_payload_json = json.dumps(segment_payload)

        #emitting payload to client for TTS
        emit("caption", {'asr' : asr, 'segment': segment_payload_json }, broadcast=True, room = room)
    else:
        print("Nothing to be emitted")

###############################################
# JOINING/LEAVING SESSIONS
###############################################
@socketio.on("join")
def on_join(data):
    user = data["user"]
    room = data["room"]
    print(f"client {user} wants to join: {room}")
    join_room(room)
    emit("caption", f"User {user} joint event {room},", room=room)

@socketio.on('leave')
def on_left(data):
    user = data["user"]
    room = data["room"]
    print(f"client {user} wants to leave: {room}")
    leave_room(room)
    emit("caption", f"User {user} left event {room},", room=room)

def segment(text, final):
    print("Calling Segmentation API")

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    logline = str(current_time) + '\t' + 'CALLING SEGMENTER'
    logfile.write(logline)
    logfile.write("\n")

    #API endpoint
    #endpoint = 'http://127.0.0.1:8000/parse' # local version
    endpoint = 'https://asr-api.meetkudo.com/parse' #web version

    #constructing parameters for call. tl should contain more languages
    pload = {'text': text, 'final': final}

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S.%f")
        logline = str(current_time) + '\t' + 'RESPONSE SEGMENTER\t' + str(result)
        logfile.write(logline)
        logfile.write("\n")

        return result
    else:
        result = {"error": response}


def translate(text, tl):
    print("Calling Translation API")

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    logline = str(current_time) + '\t' + 'CALLING TRANSLATOR'
    logfile.write(logline)
    logfile.write("\n")

    #Azure endpoint
    endpoint = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0'
    subscription_key = '830a4539e6914c8ea68e4b912ca678af'
    region = 'eastus'

    #constructing parameters for call. tl should be list containing more languages
    sl = 'en'
    params = "&from=" + sl + "&to=" + tl 

    constructed_url = endpoint + params

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # You can pass more than one object in body.
    body = [{
        'text' : text
    }]
    request = requests.post(constructed_url, headers=headers, json=body)
    response = request.json()

    translation_list = response[0]['translations']
    for translation_language in translation_list:
        translation = translation_language['text']
        print('Translation: ' + translation)

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S.%f")
        logline = str(current_time) + '\t' + 'RESULT TRANSLATOR' + str(translation)
        logfile.write(logline)
        logfile.write("\n")

        return translation

if __name__ == "__main__":
    socketio.run(app, debug=True)