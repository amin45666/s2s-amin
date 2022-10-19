from datetime import datetime

from datamatrix import DataMatrix

from api import paraphrase, segment, translate

# Initializate DataMatrix for logging time of segments in a session
# TO DO: This needs to become Session dependent
# TO DO: Probably move it to simple dictionary and save it in cache
dm = DataMatrix(length=10)  # row number is 10 just for testing
dm.timestamp_end_SL = "undef"
dm.duration_seg_SL = "undef"
dm.duration_seg_TL = "undef"  # TO DO: this should be for each target language
dm.nr_word_TL = "undef"
dm.delay_TL = "undef"
print(dm)

#################
# SESSION LOGGING
#################
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
