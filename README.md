# THIS REPOSITORY WILL MOVE INTO KUDO'SPACE

# KUDO STS - API

This is the S2S API for speech-to-speech translation.

The API provide a progammatical way to access the S2S service.

This API contains three entry points:

- /parse: to continuously send transcription in Json and receive translated short sentences to convert to speech
- /startSession: to initialize a session with a unique ID
- /stopSession: to flush the session

# Local installation

cd this-app-folder
pip install -r requirements.txt

Note: Requires python 3.9 for compatibility reasons with eventlet

# Local configuration

- Add .env file

# How to run locally

- cd into app
- uvicorn main:app
- click on Connect and start speaking in the mic (allow permissions)

Note: as default, the API will use the Segment Segmenter deployed on the Web. If you want to use a local version of the Sentence Segmenter, run it in a new Terminal following the instructions indicated in its respective repo. Adapt Endpoint in app.py (search for #API endpoint) to local.

# Deployment on Heroku with git

heroku login
git push heroku main

# I/O API

As input it accepts a JSON payload:

```
{'asr': 'transcription text', 'status': 'azure_flag
temporary/final/silence', 'room': 'session_id', 'sourceLanguage': 'the
source language', 'targetTanguages': 'the target languages' }
```

It responds with a JSON payload:

```
{'asr': 'original transcription text', 'segment':
'{'en' : 'translation in english', 'fr': 'translation in french'}',
'voiceSpeed' : '{'en' : '10', 'fr': '20'}, 'voiceStyle': 'this is the style of the voice for TTS'}
```

# Session initialisation

To initialize a session, call

```
/api/startSession/<sessionId>
```

where <sessionId> is your unique session ID

# API Info

- initialize a session with `/startSession<sessionId>` This is a GET request
- send payload to `/parse` This is POST request. Note that the ID needs to be sent in any call, see dedicated parameter in payload. This allws the API to be stateless

Note: `test/parseAPItest.pl` tests the API simulating a new session and sending continuously AZURE transcripts to the API.
