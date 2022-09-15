let subscriptionKey;
let serviceRegion = "eastasia";
let authorizationToken = "";
let SpeechSDK;
let synthesizer;
let player;
let audioConfig;
let ttsToken;
let speechCounter = 0;
let recognizer;
let recognizer_status = 'off';
let statusService = 'undef';

function intialize() {
        console.log("Initialize APP 5");
        if (!!window.SpeechSDK) {
            SpeechSDK = window.SpeechSDK;
        } else {
            console.log("error with SpeechSDK");
        }
}

function fromMic() {
	let speechConfig;
	let languageOptions;

	if (ttsToken) {
	  speechConfig = SpeechSDK.SpeechTranslationConfig.fromAuthorizationToken(
		ttsToken,
		"eastus"
	  );
	} else {
	  subscriptionKey = "6af6abea507a4e09ae379b22e79ef25a";
	  speechConfig = SpeechSDK.SpeechTranslationConfig.fromSubscription(
		subscriptionKey,
		"eastus"
	  );
	}
		
    // Set the source language.
    languageOptions = document.getElementById("sourceLanguage");
    speechConfig.speechRecognitionLanguage = languageOptions.value;
	
    let audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
    
    console.log('Speak into your microphone.');    
	
	recognizer.recognizing = (s, e) => {
		console.log(`ASR RECOGNIZING: Text=${e.result.text}`);
		document.getElementById("ASR").innerHTML = e.result.text;
		var sessionId = document.getElementById("sessionId").innerHTML; 
		let asr = e.result.text
		//force socket to emit a value otherwise APP complains
		if (!asr) {
			asr = " "
		}
        socket.emit('message', {'asr': asr, 'final': 'False', 'room': sessionId});
	};
	
	recognizer.recognized = (s, e) => {
		//if (e.result.reason == ResultReason.RecognizedSpeech) {
			console.log(`ASR RECOGNIZED: Text=${e.result.text}`);
			document.getElementById("ASR").innerHTML = e.result.text;
	    	var sessionId = document.getElementById("sessionId").innerHTML; 
			let asr = e.result.text
			//force socket to emit a value otherwise APP complains
			if (!asr) {
					asr = " "
			}
            socket.emit('message', {'asr': asr, 'final': 'True', 'room': sessionId});
		//}
		//else if (e.result.reason == ResultReason.NoMatch) {
		//	console.log("NOMATCH: Speech could not be recognized.");
		//}
	};
	
	recognizer.canceled = (s, e) => {
		console.log(`ASR CANCELED: Reason=${e.reason}`);

		if (e.reason == CancellationReason.Error) {
			console.log(`"CANCELED: ErrorCode=${e.errorCode}`);
			console.log(`"CANCELED: ErrorDetails=${e.errorDetails}`);
			console.log("CANCELED: Did you update the subscription info?");
		}

		recognizer.stopContinuousRecognitionAsync();
		recognizer_status='off';
	};

	recognizer.startContinuousRecognitionAsync();
}

function record(){
	console.log('RECOGNIZER STATUS: ' + recognizer_status);
	
	//renewing Authorisation in 5 minutes 

	if ( recognizer_status == 'off') {
		console.log("starting service");
		recognizer_status = 'on';
		console.log('RECOGNIZER NEW STATUS: ' + recognizer_status);

		document.getElementById("recordButton").innerHTML = " Stop session";//button
		document.getElementById("ASR").innerHTML = "Start session";//message

		joinRoom();
		fromMic();
	}
	else{
		console.log("stopping service");
		recognizer_status = 'off';
		console.log('RECOGNIZER NEW STATUS: ' + recognizer_status);

		document.getElementById("recordButton").innerHTML = " Connect ";//button
		document.getElementById("ASR").innerHTML = "Stop listening";//message
		recognizer.stopContinuousRecognitionAsync();
		

		leaveRoom();
	}

}


