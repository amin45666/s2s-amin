# KUDO STS - Pipeline

This POC is using AZURE ASR to transcribe the mic input, then it sends the transcription to the API Segmenter and displays the results in the UI. The API Segmenter is available here: https://github.com/fantinuoli/kudo-segmenter The API Segmenter needs to be deployed locally and run.

# How to run
- Run the API segmenter locally as indicated in the repo
- cd into app, $ python app.py, in browser http://127.0.0.1:5000/sts-next 
- click on Connect and start speaking in the mic (allow permissions)

# Logfile

## V.01
First version
