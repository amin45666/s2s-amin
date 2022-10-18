import flask
from flask import Flask, flash, Response, redirect, send_file, url_for, request, session, abort, render_template, make_response, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from decorators import roles_required
import os
import json
import requests, uuid
import random
import string
from datetime import datetime
from datamatrix import DataMatrix
from flask_caching import Cache

app = flask.Flask(__name__)
app.secret_key = 'jhgwjhdgwjhd3d'
socketio = SocketIO(app)

#switch to make log of session for the moment temporary until this is not finalized
CK_log_session = False

#change this if you want to run the local Segmenter API instead of the deployed version
#SEGMENTERAPI = 'http://127.0.0.1:8000' # local version
SEGMENTERAPI = 'https://asr-api.meetkudo.com' #web version

# the real APP should send an initialisation payload with sl and list of tl
# TO DO: mimic here a json payload
sl = 'en'
tls_list = ['es', 'it', 'he', 'ar', 'fr', 'pt']


# Instantiate the cache. This is the place to store Session dependent information
# We save now the progressive number of ASR callback to log data
cache = Cache()
cache.init_app(app=app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 36000})

# Initializate DataMatrix for logging time of segments in a session
# TO DO: This needs to become Session dependent
# TO DO: Probably move it to simple dictionary and save it in cache
dm = DataMatrix(length=10) # row number is 10 just for testing
dm.timestamp_end_SL = 'undef'
dm.duration_seg_SL  = 'undef'
dm.duration_seg_TL  = 'undef' # TO DO: this should be for each target language
dm.nr_word_TL       = 'undef'
dm.delay_TL         = 'undef'
print(dm)

###############################################
# WELCOME
###############################################
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        form_data = request.form.to_dict()
        email = form_data.get("email", None)
        password = form_data.get("password", None)
        if email and password:
            app.logger.info(f"User email: {email}")
            response = login_authentication(email, password)
            if response['status'] in ['user unkown', 'not allowed']:
                flash('Invalid username or password')
                return redirect(url_for('login'))
            else:
                session.clear()
                session["role"] = response['role']
                return redirect(url_for(session["role"]))
        else:
            flash('Empty username or password')
            return redirect(url_for('login'))
    return render_template('login.html', title='Login')

# this is the default SENDER view. Opening this page generates a session ID, initializes the Segmenter API with the session ID and creates the view
@app.route("/sender", methods=["GET", "POST"])
@roles_required("sender")
def sender():

    # create a random session ID
    sessionId = id_generator()

    #initiate a new session of API
    initialize_segmenterAPI(sessionId)
    cache.set(sessionId, 0)

    return render_template('sender.html', sessionId=sessionId, languages=tls_list)

# this is the advanced SENDER view (with testing options). Opening this page generates a session ID, initializes the Segmenter API with the session ID and creates the view
@app.route("/consolle", methods=["GET", "POST"])
@roles_required(["sender"])
def consolle():

    # create a random session ID
    sessionId = id_generator()

    #initiate a new session of API
    initialize_segmenterAPI(sessionId)
    cache.set(sessionId, 0)

    return render_template('consolle.html', sessionId=sessionId, languages=tls_list)

# this is the receiver view which will receive the translation and the interpretation
@app.route("/receiver", methods=["GET", "POST"])
def receiver():

    return render_template("receiver.html", languages=tls_list)

# this route returns info on the version log
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
        {'minor version': 16, 'details': 'adds multilingual support', 'date': '2022-09-22'},
        {'minor version': 17, 'details': 'adding new timer logic', 'date': '2022-09-29'},
        {'minor version': 18, 'details': 'adding controller of voice speed in SENDER', 'date': '2022-10-02'},
        {'minor version': 19, 'details': 'new control of session initialisation for segmentation API', 'date': '2022-10-05'},
        {'minor version': 20, 'details': 'improved responsivness of RECEIVER', 'date': '2022-10-06'},
        {'minor version': 21, 'details': 'adding simple SENDER page with standard settings', 'date': '2022-10-12'},
        {'minor version': 22, 'details': 'adding simple login page', 'date': '2022-10-13'},
        {'minor version': 23, 'details': 'cleaning code', 'date': '2022-10-17'},
        {'minor version': 24, 'details': 'fix stop translation after 10 segments', 'date': '2022-10-18'},

    ]

    return Response(json.dumps(changelog),  mimetype='application/json')

###############################################
# LIVE
###############################################

#this is the orchestrator which is continuously called with the transcription and metadata
@socketio.on("message")
def orchestrator(data):
    #the orchestrator is receiving the transcription stream and a series of metadata associated to a session
    asr_text          = data['asr']                 #transcription
    asr_status        = data['status']              #this is the status of ASR (temporary/final/silence)
    sessionID         = data['room']                #session ID
    paraphraseFeature = data['paraphraseFeature']   #enable paraphrasing feature
    voiceSpeed        = data['voiceSpeed']          #force a voice speed (default = 1, otherwise changed by orchestrator)
    ck_lang           = data['ck_lang']             #use only 1 target language or many - should be changed with a list of required languages

    #getting the progressive callback number for this session
    counterCALLBACK = cache.get(sessionID)
    print("\nOrchestrator has been called for session: " + str(sessionID) + " and callback number: " + str(counterCALLBACK))
    print(f"Data received from SENDER:\n\ttext: '{asr_text}'\n\tstatus: '{asr_status}'\n\tsession: '{sessionID}'\n\tspeed: '{voiceSpeed}'")

    #SETTING DEFAULTS IF NO WALUES ARE PASSED
    # TO DO: there must be a better way to set defaults
    if voiceSpeed == '':
        voiceSpeed = 10 #default value
        print("No voice speed was passed, setting to default: " + str(voiceSpeed))
    
    # send asr to segmenter and see if there is a response
    mysegment = segment(asr_text, asr_status, sessionID)
    
    # recording timestamp when SL has been received
    if CK_log_session:
        log_timestamp_SL(counterCALLBACK)

    # proceed only if the Segmentator has returned a segment
    if mysegment:
        print("DATA received from SEGMENTER:\n\ttext: " + mysegment)

        paraphrasedAPPLIED = ''# this variable keeps track if the paraphrasing has been applied or not

        # deciding if a segment needs to be paraphrased (typically to improve readibility and make it shorter)
        if paraphraseFeature:
            countOfWords = len(mysegment.split())
            # we paraphrase only long segments for now. This parameter should be moved to Orchestrator default settings
            if countOfWords > 20:
                mysegment = paraphrase(mysegment, sl)
                print("Paraphrase returned: ")
                print(mysegment)
                paraphrasedAPPLIED = 'TRUE'

        # deciding in which languages to translate. For semplicity reasons, it is now either ES or ALL supported languages
        # rewrite passing a list of languages
        tls_list_send = ['']
        if ck_lang != 'all':
            tls_list_send = ['es']
        else: 
            tls_list_send = tls_list

        # translating the segment in target languages
        mytranslations = translate(mysegment, tls_list_send)

        #estimate time of TTS based on language and speed of voice
        #create session matrix with segment Nr + Duration SL + estimation in TL

        print("Translations returned: ")
        print(mytranslations)

        if CK_log_session:
            log_duration_TL(counterCALLBACK, mytranslations, voiceSpeed)

        #updating number of callback for this session
        counterCALLBACK=counterCALLBACK+1
        cache.set(sessionID, counterCALLBACK)

        mytranslations_json = json.dumps(mytranslations)

        #emitting payload to client for TTS
        print("Emitting payload to receiver")
        emit("caption", {'asr' : asr_text, 'segment': mytranslations_json, 'paraphraseFeature': paraphrasedAPPLIED, 'voiceSpeed': voiceSpeed}, broadcast=True, room = sessionID)

###############################################
# JOINING/LEAVING SESSIONS
###############################################
@socketio.on("join")
def on_join(data):
    user      = data["user"]
    sessionID = data["room"]
    print(f"client {user} wants to join: {sessionID}")
    join_room(sessionID)
    emit("caption", f"User {user} joint event {sessionID},", room=sessionID)

@socketio.on('leave')
def on_left(data):
    user      = data["user"]
    sessionID = data["room"]
    print(f"client {user} wants to leave: {sessionID}")
    leave_room(sessionID)

    emit("caption", f"User {user} left event {sessionID},", room=sessionID)

# this inizializes a session of the Segmenter for this specific Session ID
def initialize_segmenterAPI(sessionID):

    #we initialize the session with some parameters. The most important is the Session ID
    pload = {'lang': 'en', 'min_one_noun': True, 'remove_adv': False, 'delay': 3, 'sessionID': sessionID}
    endpoint = SEGMENTERAPI + '/startSession'

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        print("Initializing API: " + str(result))
        return result
    else:
        print("Error initializing of API: " + str(response))
        result = 'API initialisation error'

# this calls the Segmenter
def segment(text, asr_status, sessionID):
    print("Calling Segmentation API")

    #constructing parameters for call. tl should contain more languages
    pload = {'text': text, 'status': asr_status, 'sessionID': sessionID}
    endpoint = SEGMENTERAPI + '/parse'

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        mysegment=''
        try:
            mysegment = result[0]
        except:
            print("SEGMENTER did not return any segment")
        return mysegment
    else:
        result = {"error": response}
        return result

# this calls the translation API (now AZURE)
def translate(text, tl_list):
    print("Calling Translation API")

    #Azure endpoint
    endpoint = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0'
    subscription_key = '830a4539e6914c8ea68e4b912ca678af'
    region = 'eastus'

    #constructing language parameters for call
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

    # You can pass more than one object in body
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

# this calls the paraphrasing LM which is now a huggingface model hosted on their servers
# we may switch to other models. We may want to host it ourselves
def paraphrase(text, sl):
    print("Calling Paraphrasing API")
    API_URL = "https://api-inference.huggingface.co/models/prithivida/parrot_paraphraser_on_T5"
    headers = {"Authorization": "Bearer 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"}

    payload = {'inputs': text}
    response = requests.post(API_URL, headers=headers, json=payload)
    paraphrased_dic = response.json()
    paraphrased = paraphrased_dic[0]["generated_text"]

    return paraphrased

# simple hardcoded loging to avoid undesired eyes
def login_authentication(email, password):

    #hardcoded login for quick check
    if email == 'admin@gmail.com' and password == 'kudoadmin2022#':
        response = {
            "status": "allowed",
            "role": "sender",
            }
        return response
    else:
        response = {
            "status": "user unkown",
            "role": "sender",
            }
        return response

#################
# SESSION LOGGING
#################
def log_timestamp_SL(counterCALLBACK):
    
    dt = datetime.now()
    ts = datetime.timestamp(dt)
    dm.timestamp_end_SL[counterCALLBACK] = ts

    # recording duration SL as difference between this timestamp and previous one
    if counterCALLBACK > 0:
        SL_previous_timestamp = dm.timestamp_end_SL[counterCALLBACK-1]
        duration_seg_SL = (ts - SL_previous_timestamp) * 1000
        dm.duration_seg_SL[counterCALLBACK] = duration_seg_SL

def log_duration_TL(counterCALLBACK, mytranslations, TTS_speed):
    #recording estimated duration of TL based on number of words
    TTS_speed=1 #TO DO: harmonize this value passed here to our formula
    languageTL = "es"
    translation = mytranslations[languageTL] # this needs to be done for each TL that has been processed
    word_list = translation.split()
    number_of_words = len(word_list)
    dm.nr_word_TL[counterCALLBACK] = number_of_words

    #calculating duration        
    language_dependend_duration_coefficient = {
        'en' : 1,
        'fr' : 1,
        'it' : 1,
        'de' : 1,
        'es' : 1,
        'pt' : 1
    }

    duration_seg_TL = number_of_words * language_dependend_duration_coefficient[languageTL] * TTS_speed * 1000 # expressed in milliseconds
    dm.duration_seg_TL[counterCALLBACK] = duration_seg_TL
    print(dm)

# this generates our session ID
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

if __name__ == "__main__":
    socketio.run(app, debug=True)