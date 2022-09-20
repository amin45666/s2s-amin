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
let targetLanguageAbb;
let speechConfig;
let spokenData = [];

function intialize() {
  console.log("initialize");

  //CHECKING BROWSER SINCE AZURE NOT WORKING ON ALL BROWSERS
  if (
    (navigator.userAgent.indexOf("Opera") ||
      navigator.userAgent.indexOf("OPR")) != -1
  ) {
    alert("This browser is not supported. You need to use CHROME");
  } else if (navigator.userAgent.indexOf("Chrome") != -1) {
  } else if (navigator.userAgent.indexOf("Safari") != -1) {
    alert("This browser is not supported. You need to use CHROME");
  } else if (navigator.userAgent.indexOf("Firefox") != -1) {
    alert("This browser is not supported. You need to use CHROME");
  } else if (
    navigator.userAgent.indexOf("MSIE") != -1 ||
    !!document.documentMode == true
  ) {
    alert("This browser is not supported. You need to use CHROME");
  } else {
    alert("This browser is not supported. You need to use CHROME");
  }

  if (!!window.SpeechSDK) {
    SpeechSDK = window.SpeechSDK;
    ttsButtonState = "starting";

  } else {
    ttsButtonState = "error";
    console.log("error with SpeechSDK", !!window.SpeechSDK);
  }
}

function initializeService(TL) {
  if (ttsToken) {
    speechConfig = SpeechSDK.SpeechTranslationConfig.fromAuthorizationToken(
      ttsToken,
      "eastus"
    );
  } else {
    subscriptionKey = "6af6abea507a4e09ae379b22e79ef25a";
    speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
      subscriptionKey,
      "eastus"
    );
  }

  try {
    speechConfig.speechSynthesisLanguage = TL.split(" ")[0];
    speechConfig.speechSynthesisVoiceName = TL.split(" ")[1];
  } catch (error) {
    console.log(error);
  }

  synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig);
}

async function speak(inputText, targetLanguageAbb, voice_type='en-US-JennyNeural', voice_speed=1, voice_style='sad') {
  console.log("Inizialising config");
  console.log("Speaking: " + inputText);
  console.log("in lang: " + targetLanguageAbb);
  console.log("voice type: " + voice_type);
  console.log("voice style: " + voice_style);
  console.log("voice speed: " + voice_speed);

  const ssml = `<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="${targetLanguageAbb}">
  <voice name="${voice_type}">
  <mstts:express-as style="${voice_style}">
  <prosody rate="${voice_speed}%" pitch="0%">
  ${inputText}
  </prosody>
  </mstts:express-as>
  </voice>
  </speak>`;


  await synthesizer.speakSsmlAsync(
    ssml,
    result => {
        if (result.errorDetails) {
            console.error(result.errorDetails);
        } else {
            console.log(JSON.stringify(result));
        }
    },
    function (err) {
      startSpeakTextAsyncButton.disabled = false;
      document.getElementById("log").innerHTML = "Error: ";
      document.getElementById("log").innerHTML = err;
      document.getElementById("log").innerHTML = "\n";
      window.console.log(err);
    }
  );
}
