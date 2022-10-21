import json
from datetime import datetime

from datamatrix import DataMatrix

from api import paraphrase, segment, translate
from constants import SL, TLS_LIST, VOICE_SPEED_DEFAULT, VOICE_STYLE, USE_TIMING_MATRIX, SAMPLING_RATE

# TO DO: we need to use a datamatrix that can increase rows over time (np ?)
# TO DO: 'dm' needs to be inititated in /api/startSession and and be session dependent (session_settings)

dm = DataMatrix(length=10)  # row number is 10 just for testing
dm.timestamp_end_SL = "undef"
dm.duration_seg_SL = "undef"
dm.duration_seg_TL = "undef"  # TO DO: this should be for each target language
dm.nr_word_TL = "undef"
dm.delay_TL = "undef"
print(dm)

def log_duration_TL(segment_nr, mytranslations, TTS_speed):
    # recording estimated duration of TL based on number of words
    TTS_speed = 1  # TO DO: harmonize this value passed here to our formula
    languageTL = "es"
    translation = mytranslations[
        languageTL
    ]  # this needs to be done for each TL that has been processed
    word_list = translation.split()
    number_of_words = len(word_list)
    dm.nr_word_TL[segment_nr] = number_of_words

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
    dm.duration_seg_TL[segment_nr] = duration_seg_TL
    print(dm)


def log_timestamp_SL(segment_nr):

    dt = datetime.now()
    ts = datetime.timestamp(dt)
    dm.timestamp_end_SL[segment_nr] = ts

    # recording duration SL as difference between this timestamp and previous one
    if segment_nr > 0:
        SL_previous_timestamp = dm.timestamp_end_SL[segment_nr - 1]
        duration_seg_SL = (ts - SL_previous_timestamp) * 1000
        dm.duration_seg_SL[segment_nr] = duration_seg_SL


def data_orchestrator(data, cache, sourceLanguage, targetLanguages):
    asr_text          = data["asr"]        # transcription
    asr_status        = data["status"]     # this is the status of ASR (temporary/final/silence)
    sessionID         = data["room"]       # session ID
    use_rewriting     = data["rewriting"]  # enable rewriting feature
    voiceSpeed        = data["voiceSpeed"] # force a voice speed (default = 1, otherwise set by orchestrator)

    # getting the progressive callback number for this session
    session_settings = cache.get(sessionID)
    asr_callbacks = session_settings["asr_callbacks"]
    segment_nr = session_settings["segment_nr"]

    # SETTING DEFAULTS IF NO VALUES ARE PASSED
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

    '''
    call the Segmenter API with a given sampling rate. 1 is better
    '''
    mysegment = ''
    if asr_callbacks % SAMPLING_RATE == 0:
        mysegment = segment(asr_text, asr_status, sessionID, sourceLanguage)
    else:
        print("skipping this callback to save computational power. 1 is not supported by live deployment")

    '''
    continue with the NLP pipeline only if a segment has been returned
    '''
    if mysegment:
        print("Data received from SEGMENTER:\n\ttext: " + mysegment)

        # recording timestamp when SL has been received
        if USE_TIMING_MATRIX:
            log_timestamp_SL(segment_nr)
            
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

        '''
        translating the segment in target languages
        '''
        mytranslations = translate(mysegment, sourceLanguage, targetLanguages)
        print("Data returned from translator: ")
        print(mytranslations)

        if USE_TIMING_MATRIX:
            log_duration_TL(segment_nr, mytranslations, voiceSpeed)

        # updating session info in cache
        asr_callbacks = asr_callbacks + 1
        segment_nr = segment_nr + 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "segment_nr": segment_nr,
        }
        cache.set(sessionID, session_settings)

        mytranslations_json = json.dumps(mytranslations)

        payload = {
            "asr": asr_text,
            "segment": mytranslations_json,
            "paraphraseFeature": flag_rewritten,
            "voiceSpeed": voiceSpeed,
            "voiceStyle": VOICE_STYLE,
            "status": "ok",
        }

    else:
        # updating session info in cache
        asr_callbacks = asr_callbacks + 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "segment_nr": segment_nr,
        }
        cache.set(sessionID, session_settings)

        #responding with an empty status
        payload =	{
        "status": "empty",
        }

    return payload
