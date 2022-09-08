# KUDO STS - APPLICATION

This is the S2S APP for speech-to-speech translation. The FE is made of two main parts:

- /sender: uses AZURE ASR to transcribe the audio input (mic or other input audio), then it sends the transcription stream to the S2S-API (former called Segmenter) and displays the results in the UI and to connected receivers. Websockets are provided. 
- /receiver: it receives the translation from the the S2S-App backend, requests text-to-speech from Azure


# How to run
- Run the API segmenter locally as indicated in the repo
- cd into app, $ flask run, in browser http://127.0.0.1:5000/sender 
- click on Connect and start speaking in the mic (allow permissions)

The full pipeline (also receiver) should be tested with the deployed version of the S2S-App available at https://kudo-s2s.herokuapp.com/ 

# How to deploy APP on Heroku with git (staging)

In Shell/Terminal:

- heroku login
- cd applicationFolder
- git push heroku main

Should you need to deploy a different branch:

- git push heroku 'Name-Of-Branch':master


