# KUDO STS - APPLICATION

This is the S2S APP for speech-to-speech translation. The FE is made of two main parts:

- Sender: uses AZURE ASR to transcribe the audio input (mic or other input audio), then it sends the transcription stream to the S2S-API (former called Segmenter) and displays the results in the UI and to connected receivers. Websockets are provided. 
- Receiver: it receives the translation from the the S2S-App backend, requests text-to-speech from Azure

# Local installation

cd this-app-folder
pipenv install

Note: Requires python 3.9 for compatibility reasons with eventlet 

# How to run locally
- Run separately the API segmenter locally as indicated in its respective repo
- cd into app
- adapt Endpoint in app.py (search for #API endpoint) to local
- python app.py
- app is available in Browser http://127.0.0.1:5000
- click on Connect and start speaking in the mic (allow permissions)

# How to run on Web
- open Sender https://kudo-s2s-app.herokuapp.com/
- open Receiver https://kudo-s2s-app.herokuapp.com/receiver in a Chrome browser, wear headset or use a different computer to receive the interpretation

# Deployment on Heroku with git

heroku login
git push heroku main

 
