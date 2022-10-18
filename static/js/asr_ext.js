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
	let number_of_callbacks = 0;

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

	let phrases = document.getElementById("phrases");
    if (phrases !== "") {
        var phraseListGrammar = SpeechSDK.PhraseListGrammar.fromRecognizer(recognizer);
        phraseListGrammar.addPhrase(phrases.value.split(";"));
    }	
	
    console.log('Speak into your microphone.');    
	
	let myTimerSending;

	recognizer.recognizing = (s, e) => {
		console.log(`ASR TEMPORARY FEED FROM AZURE: ${e.result.text}`);
		document.getElementById("ASR").innerHTML = e.result.text;
		let sessionId = document.getElementById("sessionId").innerHTML; 
		let asr = e.result.text

		//force socket to emit a value otherwise APP complains

		if (!asr) {
			asr = " "
		}

		//simple hack to reduce number of API calls 
		let sampling_threasold = document.getElementById("delay").value;

		//set voice speed
		let voiceSpeed = document.getElementById("voiceSpeed").value;

		//switch paraphrasing feature
		let CBparaphraseFeature = document.querySelector('#paraphraseFeature');
		if (CBparaphraseFeature.checked){
			paraphraseFeature = 'TRUE'
		}

		//switch languages to default
		let CBck_lang = document.querySelector('#ck_lang');
		if (CBck_lang.checked){
			ck_lang = 'all'
		}

		clearTimeout(myTimerSending);

		//emitting only if new number of words is greater than latency in tokens compared to previous asr
		number_of_callbacks=Number(number_of_callbacks)+1;

		if (number_of_callbacks > sampling_threasold){
			console.log('Sending ASR TEMPORARY FEED to APP');
        	socket.emit('message', {'asr': asr, 'status': 'temporary', 'room': sessionId, 'paraphraseFeature': paraphraseFeature, 'ck_lang': ck_lang, 'voiceSpeed': voiceSpeed});
			number_of_callbacks=0;
		}
		
	};
	
	recognizer.recognized = (s, e) => {
		//if (e.result.reason == ResultReason.RecognizedSpeech) {
			console.log(`ASR FINAL FEED FROM AZURE: Text=${e.result.text}`);
			document.getElementById("ASR").innerHTML = e.result.text;
	    	
			let sessionId = document.getElementById("sessionId").innerHTML; 

			//set voice speed
			let voiceSpeed = document.getElementById("voiceSpeed").value;

			//switch paraphrasing feature
			let CBparaphraseFeature = document.querySelector('#paraphraseFeature');
			if (CBparaphraseFeature.checked){
				paraphraseFeature = 'TRUE'
			}

			let asr = e.result.text
			//force socket to emit a value otherwise APP complains
			if (asr) {
				console.log('Sending ASR FINAL FEED to APP');
				socket.emit('message', {'asr': asr, 'status': 'final', 'room': sessionId, 'paraphraseFeature': paraphraseFeature, 'ck_lang': ck_lang, 'voiceSpeed': voiceSpeed});
				//resetting to 0 counter for callbacks
				number_of_callbacks=0;
				myTimerSending = setTimeout(sendFlagSilence, 4000);
			}
				
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

function sendFlagSilence(){
	console.log('Sending ASR SILENCE to APP');
	console.log('####SILENCE');
	let sessionId = document.getElementById("sessionId").innerHTML; 
	socket.emit('message', {'asr': '', 'status': 'silence', 'room': sessionId, 'paraphraseFeature': '', 'ck_lang': '', 'voiceSpeed': ''});
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


