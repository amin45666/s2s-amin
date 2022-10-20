# KUDO STS - APPLICATION

This is the S2S APP for speech-to-speech translation. 

This APP contains two main parts:

- everything is eeded to run the POC, i.e. front-end, session generation, etc.
- the ORCHESTRATOR as described in the S2S documentation.


The FE is made of two main parts:

- Sender: uses AZURE ASR to transcribe the audio input (mic or other input audio), then it sends the transcription stream to the S2S-API (former called Segmenter) and displays the results in the UI and to connected receivers. Websockets are provided. 
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

# Deployment on Heroku with git

heroku login
git push heroku main

 
