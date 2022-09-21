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

# manual parameters
logFeature = '' # Set to TRUE to start logging to file
paraphraseFeature = '' # Set TRUE if you want to use LM to do paraphrasing of source segment

#SEGMENTERAPI = 'http://127.0.0.1:8000/parse' # local version
SEGMENTERAPI = 'https://asr-api.meetkudo.com/parse' #web version
SEGMENTERAPI_start_session = 'https://asr-api.meetkudo.com/startSession'

# logginf feature is very rudimentary and trows error at disconnection. It should be redone - is useful after initial experimenting - using proper Flask mechanisms.
if logFeature: 
    logfile = open('log/logAPP.txt', 'a')
    logfile.write("logline\n")

###############################################
# WELCOME
###############################################

@app.route("/", methods=["GET", "POST"])
def open_page_asr():
    
    print('OPENING SESSION')
    url_client     = '' 
    client         = 1
    langs_flat     = 'Spanish'
    languages_list = langs_flat.split(':')

    sessionId = random.randint(1000,9999)

    #initiate a new session of API
    URI = 'https://asr-api.meetkudo.com/startSession?session_id=' + str(sessionId)
    response = requests.post(url=URI)
    if response.ok:
        result = response.json()
        print("Initializing API: " + str(result))
    else:
        print("Error initializing of API: " + str(response))

    return render_template('asr.html', sessionId=sessionId, asr='asr', client=client, languages=languages_list, url_client=url_client)

@app.route("/receiver", methods=["GET", "POST"])
def open_page_receiver():

    langs_flat     = 'Spanish'

    languages_list = langs_flat.split(':')
    return render_template("receiver.html", languages=languages_list)

@app.route('/info')
def info():
    changelog = [
        {'minor version': 0, 'details': 'initial POC commit', 'date': '2022-09-14'},
        {'minor version': 1, 'details': 'adds version changelog', 'date': '2022-09-14'},
        {'minor version': 2, 'details': 'adds multichannel', 'date': '2022-09-14'},
        {'minor version': 3, 'details': 'improves UI for Sender/Receiver', 'date': '2022-09-15'},
        {'minor version': 4, 'details': 'adds automatic scrolling in Sender table', 'date': '2022-09-15'},
        {'minor version': 5, 'details': 'adds timestamp of segment processing', 'date': '2022-09-15'},
        {'minor version': 6, 'details': 'adds logfile', 'date': '2022-09-15'},
        {'minor version': 7, 'details': 'adds parameter to reduce calls of API', 'date': '2022-09-16'},
        {'minor version': 8, 'details': 'adds feature to improve accuracy with list of terms', 'date': '2022-09-17'},
        {'minor version': 9, 'details': 'improves SENDER UI; fix sampling frequency logic', 'date': '2022-09-19'},
        {'minor version': 10, 'details': 'improves Receiver UI;', 'date': '2022-09-19'},
        {'minor version': 11, 'details': 'improves sampling frequency logic from APP', 'date': '2022-09-20'},
        {'minor version': 12, 'details': 'improves UI Sender; make logging optional (hard coded switch)', 'date': '2022-09-21'},
        {'minor version': 13, 'details': 'adds optional AI rephrasing for longer sentences >20 tokens', 'date': '2022-09-21'},
        {'minor version': 14, 'details': 'adds sessionID to Segmenter API payload', 'date': '2022-09-21'},
    ]

    return Response(json.dumps(changelog),  mimetype='application/json')

###############################################
# LIVE
###############################################

@socketio.on("message")
def handleMessage(data):

    asr = data['asr']
    final = data['final']
    room = data['room']
    paraphraseFeature = data['paraphraseFeature']

    if logFeature: 
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S.%f")
        logfile.write("\n")
        logline = str(current_time) + '\t' + 'ASR received\t' + str(asr) + ' (with status: ' + final + ')'
        logfile.write(logline)
        logfile.write("\n")

    print(f"\nProcessing '{asr}' with final flag '{final}' for Session '{room}' set paraphrase to '{paraphraseFeature}'")

    #languages should be dynamic, and tl more than one
    sl = 'en'
    tl = 'es' # tl should be list containing more languages

    #send asr to segmenter and see if there is a response
    segment_sl = segment(asr, final, room)
    paraphrasedAPPLIED = ''

    if segment_sl:
        mysegment = segment_sl[0]
        print("Segment returned: " + mysegment)

        #paraphrase segment 
        if paraphraseFeature:
            countOfWords = len(mysegment.split())
            if countOfWords > 20:
                mysegment = paraphrase(mysegment, sl)
                print("Paraphrase returned: ")
                print(mysegment)
                paraphrasedAPPLIED = 'TRUE'

        #translate segment to targ languages (will be more than one tl)
        mysegment = translate(mysegment, tl)
        #translation = translate(segment_sl[0], tl)
        print("Translation returned: ")
        print(mysegment)

        #creating payload. This will need to be dynamic
        segment_payload = {
            sl : segment_sl,
            tl : mysegment
        }
        segment_payload_json = json.dumps(segment_payload)

        #emitting payload to client for TTS
        print("Emitting payload to receiver")
        emit("caption", {'asr' : asr, 'segment': segment_payload_json, 'paraphraseFeature': paraphrasedAPPLIED }, broadcast=True, room = room)
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
    
    if logFeature: 
        logfile.close()

    emit("caption", f"User {user} left event {room},", room=room)

def segment(text, final, room):
    print("Calling Segmentation API")

    if logFeature: 
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S.%f")
        logline = str(current_time) + '\t' + 'CALLING SEGMENTER\t' + text
        logfile.write(logline)
        logfile.write("\n")

    #constructing parameters for call. tl should contain more languages
    pload = {'text': text, 'final': final, 'sessionID': room}

    response = requests.post(url=SEGMENTERAPI, json=pload)
    if response.ok:
        result = response.json()

        if logFeature: 
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

    if logFeature: 
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S.%f")
        logline = str(current_time) + '\t' + 'CALLING TRANSLATOR\t' + text
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

        if logFeature: 
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S.%f")
            logline = str(current_time) + '\t' + 'RESULT TRANSLATOR\t' + str(translation)
            logfile.write(logline)
            logfile.write("\n")

        return translation

def paraphrase(text, sl):
    print("Calling Paraphrasing API")
    API_URL = "https://api-inference.huggingface.co/models/prithivida/parrot_paraphraser_on_T5"
    headers = {"Authorization": "Bearer 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"}

    payload = {'inputs': text}
    response = requests.post(API_URL, headers=headers, json=payload)
    paraphrased_dic = response.json()
    paraphrased = paraphrased_dic[0]["generated_text"]

    if logFeature: 
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S.%f")
        logline = str(current_time) + '\t' + 'RESULT PARAPHRASER\t' + str(paraphrased)
        logfile.write(logline)
        logfile.write("\n")

    return paraphrased

if __name__ == "__main__":
    socketio.run(app, debug=True)