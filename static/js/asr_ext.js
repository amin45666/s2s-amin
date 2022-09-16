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
	let number_of_words_previous = '';

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

		//simple hack to reduce number of emissions
		let delay_threasold = document.getElementById("delay").value;
		let number_of_words = WordCount(asr);
		let number_of_words_previous_with_threasold = number_of_words_previous + delay_threasold;
		console.log("settings:");
		console.log(delay_threasold);
		console.log(number_of_words);
		console.log(number_of_words_previous_with_threasold);

		//emitting only if new number of words is greater than x tokens compared to previous


		if (number_of_words > number_of_words_previous_with_threasold){
			console.log('Sending ASR to APP ad temporary feed');
        	socket.emit('message', {'asr': asr, 'final': 'False', 'room': sessionId});
			//updating reference number of words
			number_of_words_previous = number_of_words; 
		}

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
			console.log('Sending ASR to APP as finalized feed');
            socket.emit('message', {'asr': asr, 'final': 'True', 'room': sessionId});
			
			//resetting to 0 reference number of words
			number_of_words_previous=0;
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

function WordCount(str) { 
	return str.split(" ").length;
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


