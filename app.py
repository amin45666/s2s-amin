import flask
from flask import Flask, flash, Response, redirect, send_file, url_for, request, session, abort, render_template, make_response, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import os
import json
import requests, uuid
from datetime import date
import random

app = flask.Flask(__name__)
app.secret_key = 'jhgwjhdgwjhd3d'
socketio = SocketIO(app)

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

    print(f"\nProcessing '{asr}' with state '{final}' for Session '{room}'")

    #languages should be dynamic, and tl more than one
    sl = 'en'
    tl = 'es' # tl should be list containing more languages

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

    #API endpoint
    endpoint = 'https://asr-api.meetkudo.com/parse'

    #constructing parameters for call. tl should contain more languages
    pload = {'text': text, 'final': final}

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        return result
    else:
        result = {"error": response}


def translate(text, tl):
    print("Calling Translation API")
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
        return translation

if __name__ == "__main__":
    socketio.run(app, debug=True)