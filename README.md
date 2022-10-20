# KUDO STS - APPLICATION

This is the S2S APP for speech-to-speech translation. 

This APP is made of - so to say - two main parts:

- the ORCHESTRATOR API as described in the S2S documentation for integration in KUDO
- everything is eeded to run a complete PC, i.e. front-end, session generation, etc.

The FE of the POC is made of 3 views:

- Sender or Consolle: uses AZURE ASR to transcribe the audio input (mic or other input audio), then it sends the transcription stream to the S2S-API (former called Segmenter) and displays the results in the UI and to connected receivers. Websockets are provided. The Sender has only basic settings, the Consolle is for R&D
- Receiver: it receives the translation from the the S2S-App backend, requests text-to-speech from Azure

# Local installation

cd this-app-folder
pipenv install

Note: Requires python 3.9 for compatibility reasons with eventlet 

# How to run locally
- cd into app
- python app.py
- app is available in Browser http://127.0.0.1:5000
- click on Connect and start speaking in the mic (allow permissions)

Note: as default, the APP will use the Segment Segmenter deployed on the Web. If you want to use a local version of the Sentence Segmenter, run it in a new Terminal following the instructions indicated in its respective repo. Adapt Endpoint in app.py (search for #API endpoint) to local. 

# How to run on Web
- open Simple Sender https://www.s2s.meetkudo.com/
- open Advanced Sender (with testing options): https://www.s2s.meetkudo.com/consolle
- open Receiver https://www.s2s.meetkudo.com/receiver in a Chrome browser, wear headset or use a different computer to receive the interpretation

# R&D Deployment on Heroku with git

heroku login
git push heroku main

# DATA I/O

As input it accepts a JSON payload:

```{'asr': 'transcription text', 'status': 'azure_flag temporary/final/silence', 'room': 'session_id', 'sourceLanguage': 'the source language', 'target languages': 'the target languages' }```

It repsponds with a JSON payload:

```{'asr': 'original transcription text', 'segment': '{'en' : 'translation in english', 'fr': 'translation in french'}', 'voiceSpeed' : '{'en' : '10', 'fr': '20'}}```


 
