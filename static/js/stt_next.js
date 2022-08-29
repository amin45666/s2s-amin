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
let counter = 1;
let sentence = "";
let previousTextIdentity;

let segmentationAPIURL = "http://127.0.0.1:8000/parse";

function intialize() {
  console.log("initialize");
  if (!!window.SpeechSDK) {
    SpeechSDK = window.SpeechSDK;
    ttsButtonState = "starting";
  } else {
    ttsButtonState = "error";
    console.log("error with SpeechSDK");
  }
}

function initializeService() {
  let speechConfig;
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

  speechConfig.speechRecognitionLanguage = "en-US"; //source language is set to default
  let audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
  recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
}

function fromMic() {
  initializeService();

  console.log("Speak into your microphone.");

  recognizer.recognizing = (s, e) => {
    sentence = e.result.text;
    let text = `<span id='${e.result.privOffset}'>${e.result.text}</span>`;
    if (e.result.privOffset == previousTextIdentity) {
      document.getElementById(previousTextIdentity).remove();
    } else {
      previousTextIdentity = e.result.privOffset;
    }

    document.getElementById("textSpan").innerHTML += text;
    adjustContent();
    populateSegment(counter, false, sentence);
  };

  recognizer.recognized = (s, e) => {
    if (e.result.text != undefined) {
      try {
        document.getElementById(previousTextIdentity).remove();
      } catch (error) {
        console.log(error);
      }

      document.getElementById(
        "textSpan"
      ).innerHTML += `<span id='${e.result.privOffset}'>${sentence}</span>`;
      document.getElementById("textSpan").innerText += "\n";
      adjustContent();

      populateSegment(counter, true, sentence);

      counter += 1;
      sentence = "";
    }
  };

  recognizer.canceled = (s, e) => {
    console.log(`CANCELED: Reason=${e.reason}`);

    if (e.reason == CancellationReason.Error) {
      console.log(`"CANCELED: ErrorCode=${e.errorCode}`);
      console.log(`"CANCELED: ErrorDetails=${e.errorDetails}`);
      console.log("CANCELED: Did you update the subscription info?");
    }

    recognizer.stopContinuousRecognitionAsync();
  };

  recognizer.startContinuousRecognitionAsync();
}

async function populateSegment(counter, flag, sentence) {
  let payload = {
    text: sentence,
    lang: "en",
    delay: 3,
    final: flag,
  };
  payload = JSON.stringify(payload);
  let options = {
    method: "POST",
    body: payload,
    headers: {
      "Content-Type": "application/json",
    },
  };

  fetch(segmentationAPIURL, options)
    .then((res) => res.json())
    .then((data) => {
      data.reverse();
      let content = "";
      try {
        for (let i = 0; i < data.length; i++) {
          content += `<tr class='seg-${counter}'>
                <td>${data[i]}</td>
              </tr>`;
        }
      } catch (error) {
        console.log(error);
      }

      document.getElementById("segmentText").innerHTML =
        content + document.getElementById("segmentText").innerHTML;

      let mtTranslationData = [];
      for (let i = 0; i < data.length; i++) {
        mtTranslationData.push({ text: data[i] });
      }
      translatorAPI(mtTranslationData, counter, flag);
    });
}

function translatorAPI(sentence, counter, flag) {
  if (sentence.length != 0) {
    fetch(
      `https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&from=en&to=${document.getElementById("targetLanguage").value.split("-")[0]
      }`,
      {
        method: "POST",
        headers: {
          "Ocp-Apim-Subscription-Key": "830a4539e6914c8ea68e4b912ca678af",
          "Ocp-Apim-Subscription-Region": "eastus",
          "Content-type": "application/json",
        },
        body: JSON.stringify(sentence),
      }
    )
      .then((response) => response.json())
      .then(async (data) => {
        socket.emit("mt", { data, room: sessionCode, counter, flag, targetLanguage: document.getElementById("targetLanguage").value });

        let content = "";
        try {
          for (let i = 0; i < data.length; i++) {
            content += `<tr class='trans-${counter}'>
                  <td>${data[i].translations[0].text}</td>
                </tr>`;
          }
        } catch (error) {
          console.log(error);
        }

        document.getElementById("mtTranslation").innerHTML =
          content + document.getElementById("mtTranslation").innerHTML;
      });
  }
}

function adjustContent() {
  let windowHeight = 0;
  let containerHeight = 53;

  windowHeight = 1 - 1;
  windowHeight = Math.ceil(windowHeight * 10);
  windowHeight += windowHeight;

  containerHeight += (3 - 2) * 30;
  if (
    document.getElementById("textSpan").offsetHeight <=
    containerHeight - windowHeight
  ) {
    document.getElementById("resultPre").style.marginTop = 0;
  } else {
    document.getElementById("resultPre").style.marginTop = `${-(
      ((document.getElementById("textSpan").offsetHeight -
        (containerHeight - windowHeight)) /
        30) *
      1.5
    )}em`;
  }
}
