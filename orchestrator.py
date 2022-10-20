import json
from datetime import datetime

from datamatrix import DataMatrix

from api import paraphrase, segment, translate
from constants import SL, TLS_LIST, VOICE_SPEED_DEFAULT

# Initializate DataMatrix for logging time of segments in a session
# TO DO: 'dm' needs to be inititated in /api/startSession and insert it in session_settings

dm = DataMatrix(length=10)  # row number is 10 just for testing
dm.timestamp_end_SL = "undef"
dm.duration_seg_SL = "undef"
dm.duration_seg_TL = "undef"  # TO DO: this should be for each target language
dm.nr_word_TL = "undef"
dm.delay_TL = "undef"
print(dm)

def log_duration_TL(counterCALLBACK, mytranslations, TTS_speed):
    # recording estimated duration of TL based on number of words
    TTS_speed = 1  # TO DO: harmonize this value passed here to our formula
    languageTL = "es"
    translation = mytranslations[
        languageTL
    ]  # this needs to be done for each TL that has been processed
    word_list = translation.split()
    number_of_words = len(word_list)
    dm.nr_word_TL[counterCALLBACK] = number_of_words

    # calculating duration
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
    )  # expressed in milliseconds
    dm.duration_seg_TL[counterCALLBACK] = duration_seg_TL
    print(dm)


def log_timestamp_SL(counterCALLBACK):

    dt = datetime.now()
    ts = datetime.timestamp(dt)
    dm.timestamp_end_SL[counterCALLBACK] = ts

    # recording duration SL as difference between this timestamp and previous one
    if counterCALLBACK > 0:
        SL_previous_timestamp = dm.timestamp_end_SL[counterCALLBACK - 1]
        duration_seg_SL = (ts - SL_previous_timestamp) * 1000
        dm.duration_seg_SL[counterCALLBACK] = duration_seg_SL


# AMIN please move the following def to orchestrator.py (if namespace is not okay, change what is needed)
def data_orchestrator(data, cache, CK_log_session):
    # the orchestrator is receiving the transcription stream and a series of metadata associated to a session
    asr_text          = data["asr"]  # transcription
    asr_status        = data["status"]  # this is the status of ASR (temporary/final/silence)
    sessionID         = data["room"]  # session ID
    use_rewriting     = data["paraphraseFeature"]  # enable paraphrasing feature
    voiceSpeed = data["voiceSpeed"]  # force a voice speed (default = 1, otherwise changed by orchestrator)
    ck_lang = data["ck_lang"]  # use only 1 target language or many - should be changed with a list of required languages

    # getting the progressive callback number for this session
    session_settings = cache.get(sessionID)
    asr_callbacks = session_settings["asr_callbacks"]
    asr_segments = session_settings["asr_segments"]

    # SETTING DEFAULTS IF NO WALUES ARE PASSED
    if voiceSpeed == "":
        voiceSpeed = VOICE_SPEED_DEFAULT
    if use_rewriting == "":
        use_rewriting = False

    print(
        f"Data received from CLIENT:\n\tsession ID: '{sessionID}'\n\ttext: '{asr_text}'\n\tstatus: '{asr_status}'\n\tasr_callbacks: '{asr_callbacks}'\n\tvoiceSpeed: '{voiceSpeed}'"
    )

    # send asr to segmenter and see if there is a response
    mysegment = segment(asr_text, asr_status, sessionID)

    # proceed only if the Segmentator has returned a segment
    if mysegment:
        print("Data received from SEGMENTER:\n\ttext: " + mysegment)

        # recording timestamp when SL has been received
        if CK_log_session:
            log_timestamp_SL(asr_segments)
            
        flag_rewritten = (
            ""  # this is a flag for ML rewriting to show in R&D UI
        )

        '''
        deciding if a segment needs to be rewritten, now off as default
        this is in focus of R&D work
        '''
        if use_rewriting:
            countOfWords = len(mysegment.split())
            # we paraphrase only long segments for now. This parameter should be moved to Orchestrator default settings
            if countOfWords > 20:
                mysegment = paraphrase(mysegment, SL)
                print("Rewritten sentence returned: ")
                print(mysegment)
                flag_rewritten = "TRUE"

        # deciding in which languages to translate. For semplicity reasons, it is now either ES or ALL supported languages
        # rewrite passing a list of languages
        tls_list_send = [""]
        if ck_lang != "all":
            tls_list_send = ["es"]
        else:
            tls_list_send = TLS_LIST

        '''
        translating the segment in target languages
        '''
        mytranslations = translate(mysegment, tls_list_send)
        print("Data returned from translator: ")
        print(mytranslations)

        if CK_log_session:
            log_duration_TL(asr_segments, mytranslations, voiceSpeed)

        # updating number of session data in cache
        asr_callbacks = asr_callbacks + 1
        asr_segments = asr_segments + 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "asr_segments": asr_segments,
        }
        cache.set(sessionID, session_settings)

        mytranslations_json = json.dumps(mytranslations)

        payload = {
            "asr": asr_text,
            "segment": mytranslations_json,
            "paraphraseFeature": flag_rewritten,
            "voiceSpeed": voiceSpeed,
        }

        return payload

    else:

        asr_callbacks = asr_callbacks + 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "asr_segments": asr_segments,
        }
        cache.set(sessionID, session_settings)
