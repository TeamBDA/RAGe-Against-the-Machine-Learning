# ── Pipeline Setup ───────────────────────────────────────────────────────────────────────────────────────────────
# The pipeline is used to process all steps/tasks associated with this project
# NOTE: For the LLM we will use a Transformer (has fit and transform), or an Estimator (has fit and predict)
# NOTE: Pass the data through in memory rather than having to do repetitive reads
# Step 1: Process speech
# Step 2: Validate data
# Step 3: Correct data use a function wrapper to fit and transform the existing LLM API call (fnc)
# Step 4: Analytics enrichments - add new columns to the data frame with new insights (e.g., question flag, word count, char count, speech rate, speaker turn id)
# Step 5: Analyze data - analytics functions to compute metrics (e.g., total words, speaker with most words, total time per speaker, total meeting time, average time per speaker, average speech rate)
# ── END Pipeline Setup ───────────────────────────────────────────────────────────────────────────────────────────

import os
import logging
import sys
import time
from sklearn.pipeline import Pipeline as SKPipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from src.transcribe_recordings import main
from src.correct_transcription import correct_text
from src.enrich_transcriptions import load_data, add_question_flag,add_num_words,add_text_size_chars, add_speech_rate, add_speaker_turn_id, save_enriched_data
from src.validate_transcriptions import get_csv_checks, get_dtype_checks, get_timestamp_checks
from src.calculate_metrics import read_file, get_rows, total_words_num, ml_speaker_rec, ml_speaker_t, speakers_total_time, meeting_total_time, average_time_per_speaker, average_time_per_meeting, average_speech_rate, generate_report_csv

# NOTE: Pass the data through in memory rather than having to do repetitive reads

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
    
# Define logger for logging in pipeline - use   logger.info("Step 1: Loading raw data..."), logger.error("err"), logger.exception("ex")
def pipeline_logger():
    logger = logging.getlogger("Pipeline Logger")
    logger.setLevel(logging.Info)

    # Clear all logging handlers before proceeding
    if logger.hasHandlers():
        logger.handlers.clear()

    # Format the log entry
    log_format = logging.Formatter(
       fmt="%(asctime)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Saves to a txt file
    file_handler = logging.FileHandler("RAGe_pipeline.log", mode="w")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Output to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_handler)
    logger.addHandler(console_handler)

    return logger

logger = pipeline_logger()

# Now using a wrapper function to output start/input and output for logging
def wrapper_with_logging(fnc):
    # Now run wrapperlog fnc with try/catch to capture steps and any exceptions
    def wrapper_log(X):
        logger.info(f"Starting logging for step {fnc.__name__}")
        start = time.time()
        try:
            result = logger.result(fnc(X))
            elapsed_time = time.time - start
            logger.info(f"Completed step {fnc.__name__} in {elapsed_time:.3f}s")
            return 

        except Exception as e:
            elapsed_time = time.time - start
            logger.error(f"Error in pipeline step {fnc.__name__}, in {elapsed_time:.3f}s: with err {e}")
            raise
    return wrapper_log

# Define all pipeline steps to execute all functions with outputs feeding inputs (where possible)
Pipeline = Pipeline([
'process_speech', FunctionTransformer(wrapper_with_logging(main)),
'correct_transcription', FunctionTransformer(wrapper_with_logging(correct_text)),
'loaddt', FunctionTransformer(wrapper_with_logging(load_data)),
'question_flag', FunctionTransformer(wrapper_with_logging(add_question_flag)),
'add_words', FunctionTransformer(wrapper_with_logging(add_num_words)),
'add_chars', FunctionTransformer(wrapper_with_logging(add_text_size_chars)),
'add_speech', FunctionTransformer(wrapper_with_logging(add_speech_rate)),
'add_speaker_turn', FunctionTransformer(wrapper_with_logging(add_speaker_turn_id)),
'save_data', FunctionTransformer(wrapper_with_logging(save_enriched_data)),
'check_csv', FunctionTransformer(wrapper_with_logging(get_csv_checks)),
'check_dtype', FunctionTransformer(wrapper_with_logging(get_dtype_checks)),
'check_timestamp', FunctionTransformer(wrapper_with_logging(get_timestamp_checks)),
'fileread', FunctionTransformer(wrapper_with_logging(read_file)),
'retrieve_rows', FunctionTransformer(wrapper_with_logging(get_rows)),
'total_words', FunctionTransformer(wrapper_with_logging(total_words_num)),
'speaker', FunctionTransformer(wrapper_with_logging(ml_speaker_rec)),
'speaker_time', FunctionTransformer(wrapper_with_logging(ml_speaker_t)),
'speakers total time', FunctionTransformer(wrapper_with_logging(speakers_total_time)),
'check_meeting_total_time', FunctionTransformer(wrapper_with_logging(meeting_total_time)),
'compute_speak_avg_time', FunctionTransformer(wrapper_with_logging(average_time_per_speaker)),
'compute_speak_avg_meeting', FunctionTransformer(wrapper_with_logging(average_time_per_meeting)),    
'compute_rate_avg_time', FunctionTransformer(wrapper_with_logging(average_speech_rate)),
'generate_report', FunctionTransformer(wrapper_with_logging(generate_report_csv))
])
