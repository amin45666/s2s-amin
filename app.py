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
paraphraseFeature = '' # Set TRUE if you want to use LM to do paraphrasing of source segment

#SEGMENTERAPI = 'http://127.0.0.1:8000/parse' # local version
SEGMENTERAPI = 'https://asr-api.meetkudo.com/parse' #web version
SEGMENTERAPI_start_session = 'https://asr-api.meetkudo.com/startSession'

sl = 'en'
tls_list = ['es', 'it', 'he', 'ar', 'fr', 'pt']


###############################################
# WELCOME
###############################################

@app.route("/", methods=["GET", "POST"])
def open_page_asr():
    
    print('OPENING SESSION')
    url_client     = '' 
    client         = 1

    sessionId = random.randint(1000,9999)

    #initiate a new session of API
    URI = 'https://asr-api.meetkudo.com/startSession?session_id=' + str(sessionId)
    response = requests.post(url=URI)
    if response.ok:
        result = response.json()
        print("Initializing API: " + str(result))
    else:
        print("Error initializing of API: " + str(response))

    return render_template('asr.html', sessionId=sessionId, asr='asr', client=client, languages=tls_list, url_client=url_client)


@app.route("/receiver", methods=["GET", "POST"])
def open_page_receiver():

    return render_template("receiver.html", languages=tls_list)

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
        {'minor version': 14, 'details': 'adds API initialisation call with sessionID', 'date': '2022-09-21'},
        {'minor version': 15, 'details': 'minor improvements to Receiver UI', 'date': '2022-09-22'},
        {'minor version': 16, 'details': 'adds multilingual support', 'date': '2025-09-22'},
        {'minor version': 17, 'details': 'adding new timer logic', 'date': '2025-09-29'},

    ]

    return Response(json.dumps(changelog),  mimetype='application/json')

###############################################
# LIVE
###############################################

@socketio.on("message")
def handleMessage(data):

    asr = data['asr']
    status = data['status']
    room = data['room']
    ck_lang = data['ck_lang']
    paraphraseFeature = data['paraphraseFeature']

    print(f"\nProcessing '{asr}' with status flag '{status}' for Session '{room}' set paraphrase to '{paraphraseFeature}'")

    #send asr to segmenter and see if there is a response
    segment_sl = segment(asr, status, room)
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

        # translate only in default language. This should be handeld properly
        tls_list_send = ['']
        if ck_lang != 'all':
            tls_list_send = ['es']
        else: 
            tls_list_send = tls_list

        mytranslations = translate(mysegment, tls_list_send)
        print("Translations returned: ")
        print(mytranslations)

        mytranslations_json = json.dumps(mytranslations)

        #emitting payload to client for TTS
        print("Emitting payload to receiver")
        emit("caption", {'asr' : asr, 'segment': mytranslations_json, 'paraphraseFeature': paraphrasedAPPLIED }, broadcast=True, room = room)
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

def segment(text, status, room):
    print("Calling Segmentation API")

    #constructing parameters for call. tl should contain more languages
    pload = {'text': text, 'status': status, 'sessionID': room}

    response = requests.post(url=SEGMENTERAPI, json=pload)
    if response.ok:
        result = response.json()
        return result
    else:
        result = {"error": response}

def translate(text, tl_list):
    print("Calling Translation API")

    #Azure endpoint
    endpoint = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0'
    subscription_key = '830a4539e6914c8ea68e4b912ca678af'
    region = 'eastus'

    #constructing parameters for call
    sl = 'en'
    params = "&from=" + sl
    for tl in tl_list:
        params = params + "&to=" + tl 
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
    translations_list = response[0]['translations']

    #create response data structure
    translations={sl:text}
    for translation_language in translations_list:
        translation = translation_language['text']
        language = translation_language['to']
        translations[language] = translation

    return translations

def paraphrase(text, sl):
    print("Calling Paraphrasing API")
    API_URL = "https://api-inference.huggingface.co/models/prithivida/parrot_paraphraser_on_T5"
    headers = {"Authorization": "Bearer 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"}

    payload = {'inputs': text}
    response = requests.post(API_URL, headers=headers, json=payload)
    paraphrased_dic = response.json()
    paraphrased = paraphrased_dic[0]["generated_text"]

    return paraphrased

if __name__ == "__main__":
    socketio.run(app, debug=True)