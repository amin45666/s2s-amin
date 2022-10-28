import json
from datetime import datetime

from datamatrix import DataMatrix
from dependency import logging
from localStoragePy import localStoragePy

from s2s.constants import (
    SAMPLING_RATE,
    SL,
    TLS_LIST,
    USE_TIMING_MATRIX,
    VOICE_SPEED_DEFAULT,
    VOICE_STYLE,
    DEFAULT_VOICES_NAME,
)
from s2s.service import paraphrase, segment, translate

localStorage = localStoragePy("s2s", "json")

# TO DO: we need to use a datamatrix that can increase rows over time (np ?)
# TO DO: 'dm' needs to be initiated in /api/startSession and and be session dependent (session_settings)

dm = DataMatrix(length=10)  # row number is 10 just for testing
dm.timestamp_end_SL = "undef"
dm.duration_seg_SL = "undef"
dm.duration_seg_TL = "undef"  # TO DO: this should be for each target language
dm.nr_word_TL = "undef"
dm.delay_TL = "undef"
print(dm)


def log_duration_TL(segment_nr, mytranslations, TTS_speed):
    """
    Record estimated duration of TL based on number of words

    Parameters
    ----------
    segment_nr
    mytranslations: list of translated text
    TTS_speed: speed of voice while converting text to speech

    Returns
    -------
    None
    """

    TTS_speed = 1
    languageTL = "es"
    translation = mytranslations[languageTL]
    word_list = translation.split()
    number_of_words = len(word_list)
    dm.nr_word_TL[segment_nr] = number_of_words

    language_dependend_duration_coefficient = {
        "en": 1,
        "fr": 1,
        "it": 1,
        "de": 1,
        "es": 1,
        "pt": 1,
    }

    duration_seg_TL = (
        number_of_words
        * language_dependend_duration_coefficient[languageTL]
        * TTS_speed
        * 1000
    )
    dm.duration_seg_TL[segment_nr] = duration_seg_TL
    print(dm)


def log_timestamp_SL(segment_nr):
    """
    Record estimated duration of SL between current timestamp and previous one

    Parameters
    ----------
    segment_nr

    Returns
    -------
    None
    """

    dt = datetime.now()
    ts = datetime.timestamp(dt)
    dm.timestamp_end_SL[segment_nr] = ts

    if segment_nr > 0:
        SL_previous_timestamp = dm.timestamp_end_SL[segment_nr - 1]
        duration_seg_SL = (ts - SL_previous_timestamp) * 1000
        dm.duration_seg_SL[segment_nr] = duration_seg_SL


def data_orchestrator(data, sourceLanguage, targetLanguages):
    """
    Calls the segmenter API with given sampling rate and continue with NLP pipeline only if a segment is returned.
    Deciding if a segment needs to be rewritten, now off as default this is in focus of R&D work. And finally translates the segments.

    Parameters
    ----------
    segment_nr
    sourceLanguage: source language
    targetLanguage: targetLanguage

    Returns
    -------
    asr: original text,
    segment: segment of text,
    paraphraseFeature: paraphrase feature,
    voiceSpeed: speed of voice while converting text to speech,
    voiceStyle: voice's style,
    status: status of response

    OR

    status : status of response
    """
    asr_text = data["asr"]
    asr_status = data["status"]
    sessionID = data["room"]
    use_rewriting = data["rewriting"]
    voiceSpeed = data["voiceSpeed"]

    local_data = str(localStorage.getItem("sessionId")).replace("'", '"')
    if local_data:
        session_settings = json.loads(local_data)
        asr_callbacks = session_settings["asr_callbacks"]
        segment_nr = session_settings["segment_nr"]
    else:
        asr_callbacks = 0
        segment_nr = 0

    if voiceSpeed == "":
        voiceSpeed = VOICE_SPEED_DEFAULT
    if use_rewriting == "":
        use_rewriting = False
    if targetLanguages == "":
        targetLanguages = TLS_LIST
    if sourceLanguage == "":
        sourceLanguage = SL

    print(
        f"Data received from CLIENT:\n\tsession ID: '{sessionID}'\n\ttext: '{asr_text}'\n\tstatus: '{asr_status}'\n\tasr_callbacks: '{asr_callbacks}'\n\tvoiceSpeed: '{voiceSpeed}'"
    )
    # logging.info("Orchestrator")
    # logging.warning("Orchestrator")
    # logging.error("Orchestrator")
    mysegment = ""
    if asr_status == 'temporary':
        if asr_callbacks % SAMPLING_RATE == 0:
            mysegment = segment(asr_text, asr_status, sessionID, sourceLanguage)
        else:
            print(
                "skipping this callback to save computational power. 1 is not supported by live deployment"
            )
    else:
        mysegment = segment(asr_text, asr_status, sessionID, sourceLanguage)

    if mysegment:
        print("Data received from SEGMENTER:\n\ttext: ", mysegment)

        if USE_TIMING_MATRIX:
            log_timestamp_SL(segment_nr)

        flag_rewritten = ""

        if use_rewriting:
            countOfWords = len(mysegment.split())
            if countOfWords > 20:
                mysegment = paraphrase(mysegment, SL)
                print("Rewritten sentence returned: ")
                print(mysegment)
                flag_rewritten = "TRUE"

        mytranslations = translate(mysegment, sourceLanguage, targetLanguages)
        print("Data returned from translator: ")
        print(mytranslations)

        if USE_TIMING_MATRIX:
            log_duration_TL(segment_nr, mytranslations, voiceSpeed)

        asr_callbacks = asr_callbacks + 1
        segment_nr = segment_nr + 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "segment_nr": segment_nr,
        }
        localStorage.setItem("sessionId", session_settings)

        mytranslations_json = json.dumps(mytranslations)

        payload = {
            "asr": asr_text,
            "segment": mytranslations_json,
            "paraphraseFeature": flag_rewritten,
            "voiceSpeed": voiceSpeed,
            "voiceStyle": VOICE_STYLE,
            "voiceName": {
                language_code: DEFAULT_VOICES_NAME[language_code]
                for language_code in targetLanguages
            },
            "status": "ok",
        }

    else:
        asr_callbacks = asr_callbacks + 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "segment_nr": segment_nr,
        }
        localStorage.setItem("sessionId", session_settings)

        payload = {
            "status": "empty",
        }

    return payload
