# ── Pipeline Setup ───────────────────────────────────────────────────────────────────────────────────────────────
# The pipeline is used to process all steps/tasks associated with this project
# NOTE: For the LLM we will use a Transformer (has fit and transform), or an Estimator (has fit and predict)
# Step 1: Process speech
# Step 2: Validate data
# Step 3: Correct data use a function wrapper to fit and transform the existing LLM API call (fnc)
# Step 4: Analyze data
#
#
#
#
#
#
#
#
#
# ── END Pipeline Setup ───────────────────────────────────────────────────────────────────────────────────────────

import os
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from models.Speech2Text import main
from transcription.Invoke_Validation_Checks import get_csv_checks, get_dtype_checks, get_timestamp_checks
from transcription.correct_transcription import correct_text
from analytics.enrichments import load_data, add_question_flag,add_num_words,add_text_size_chars, add_speech_rate, add_speaker_turn_id(df)
from analytics.Metrics import total_words_num, top_speaker, bot_speaker, speakers_total_time, meeting_total_time, average_time_per_speaker,average_speech_rate

# ── Project Path Setup ────────────────────────────────────────────────────────────────
# Determine project root (folder above this script)
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the /data directory
OTHER_DIR = os.path.join(BASE_DIR, "data")
# ── END Project Path Setup - START Pipeline Tasks──────────────────────────────────────

class Correction2Text(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return correct_text(X)

# Define all pipeline steps to execute all functions with outputs feeding inputs (where possible)
Pipeline = Pipeline([
'process_speech', FunctionTransformer(main, validate=True),
'check_csv', FunctionTransformer(get_csv_checks, validate=True),
'check_dtype', FunctionTransformer(get_dtype_checks, validate=True),
'check_timestamp', FunctionTransformer(get_timestamp_checks, validate=True),
'repurpose_text', FunctionTransformer(correct_text, validate=True),
'total_words', FunctionTransformer(total_words_num, validate=True),
'check_top_speaker', FunctionTransformer(top_speaker, validate=True),
'check_bot_speaker', FunctionTransformer(bot_speaker, validate=True),
'check_speak_total_time', FunctionTransformer(speakers_total_time, validate=True),
'check_meeting_total_time', FunctionTransformer(meeting_total_time, validate=True),
'compute_speak_avg_time', FunctionTransformer(average_time_per_speaker, validate=True),
'compute_rate__avg_time', FunctionTransformer(average_speech_rate, validate=True)
])
