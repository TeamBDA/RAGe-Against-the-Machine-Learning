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
import datetime
import os
import logging
import sys
import time
from vosk import Model
from google import genai
from docx import Document
import pandas as pd
from sklearn.pipeline import Pipeline as SKPipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.base import BaseEstimator, TransformerMixin

# ───────────────────────────────────────────────────────────────
# IMPORTS FROM PROJECT MODULES
# ───────────────────────────────────────────────────────────────
from src.transcribe_recordings import (
    get_wav_duration_seconds,
    check_ffmpeg,
    parse_filename,
    convert_to_wav,
    transcribe_wav,
    MODEL_NAME
)

from src.correct_transcription import correct_text

from src.enrich_transcriptions import (
    load_data,
    add_question_flag,
    add_num_words,
    add_text_size_chars,
    add_speech_rate,
    add_speaker_turn_id,
    save_enriched_data,
    TRANSCRIPTIONS_DIR
)

from src.validate_transcriptions import (
    get_csv_checks,
    get_dtype_checks,
    get_timestamp_checks,
    PARAMS
)

from src.calculate_metrics import (
    read_file,
    get_rows,
    total_words_num,
    ml_speaker_rec,
    ml_speaker_t,
    speakers_total_time,
    meeting_total_time,
    average_time_per_speaker,
    average_time_per_meeting,
    average_speech_rate,
    questions_per_speaker,
    generate_report_csv
)

# ───────────────────────────────────────────────────────────────
# PROJECT PATHS
# ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "data/results")
LOG_FILE = os.path.join(LOG_DIR, "RAGe_pipeline.log")

# ───────────────────────────────────────────────────────────────
# TRANSCRIPTION VARIABLES
# ───────────────────────────────────────────────────────────────
m4a_path = "/data/recordings"
tmp_wav_path = "/tmp/tmp_audio.wav"
wav_path = tmp_wav_path
model = Model(model_name=MODEL_NAME)

# ───────────────────────────────────────────────────────────────
# CORRECTION VARIABLES
# ───────────────────────────────────────────────────────────────
API_KEY = input("Please enter your Google Gemini API key: ")
client = genai.Client(api_key=API_KEY)

# ───────────────────────────────────────────────────────────────
# ENRICHMENT VARIABLES
# ───────────────────────────────────────────────────────────────
input_file = os.path.join(TRANSCRIPTIONS_DIR, "corrected_transcripts.csv")
df = load_data(input_file)
output_file = os.path.join(TRANSCRIPTIONS_DIR, "enriched_transcripts.csv")

# ───────────────────────────────────────────────────────────────
# VALIDATION VARIABLES
# ───────────────────────────────────────────────────────────────
#Parameters used for the functions below, we can expand this as we add more functions and checks, and it keeps the parameters in one place for easy reference and maintenance. We can also use this to build a config file later if we want to make it more dynamic and not have to change code to update parameters.
PARAMS = {
    "csv_read": {
        "header": 0,
        "skip_blank_lines": True,
        "na_values": ["", " ", "  "]
    },

    "dtype_checks": {
        "cols_int": ['num_words', 'speech_rate_wps', 'speaker_turn_id', 'total_speaking_time_seconds'],
        "col_bool": 'question_flag'
    },

    "timestamp_checks": {
        "timestamp_col": "timestamp"
    }
}

CSV_FILE = os.path.join(TRANSCRIPTIONS_DIR, "enriched_transcripts.csv")
READ_PARAMS = PARAMS["csv_read"]
df_validation = pd.read_csv(CSV_FILE, **READ_PARAMS)

reportdoc = Document()
table = reportdoc.add_table(rows=1, cols=1)
table.style = "Table Grid"
table.rows[0].cells[0].text = "Error Description"

cols_int = PARAMS["dtype_checks"]["cols_int"]
col_bool = PARAMS["dtype_checks"]["col_bool"]
timestamp_col = PARAMS["timestamp_checks"]["timestamp_col"]

# ───────────────────────────────────────────────────────────────
# METRICS VARIABLES
# ───────────────────────────────────────────────────────────────
data = pd.read_csv(os.path.join(TRANSCRIPTIONS_DIR, "enriched_transcripts.csv"))
mode = "most"
output_filename = "meeting_report.csv"

# ───────────────────────────────────────────────────────────────
# LOGGER
# ───────────────────────────────────────────────────────────────
def pipeline_logger():
    logger = logging.getLogger("Pipeline Logger")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_format = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(LOG_FILE, mode="w")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    return logger

logger = pipeline_logger()
logger.info("Logger initialised and ready.")

# ───────────────────────────────────────────────────────────────
# WRAPPERS
# ───────────────────────────────────────────────────────────────
def check_ffmpeg_wrapper(X):
    check_ffmpeg()
    return X

def convert_to_wav_wrapper(X):
    convert_to_wav(m4a_path, tmp_wav_path)
    return X

def transcribe_wav_wrapper(X):
    return transcribe_wav(wav_path, model)

def correct_txt_wrapper(X):
    return correct_text(client, X)

def enriched_dt_wrapper(X):
    save_enriched_data(df, output_file)
    return X

def get_dtype_checks_wrapper(X):
    get_dtype_checks(df_validation, table, cols_int, col_bool)
    return X

def csv_checks_wrapper(X):
    get_csv_checks(df_validation, table)
    return X

def get_timestamp_checks_wrapper(X):
    get_timestamp_checks(df_validation, table, timestamp_col)
    return X

def ml_speaker_rec_wrapper(X):
    return ml_speaker_rec(data, mode)

def ml_speaker_t_wrapper(X):
    return ml_speaker_t(data, mode)

def generate_report_csv_wrapper(X):
    generate_report_csv(data, output_filename)
    return X

# ───────────────────────────────────────────────────────────────
# LOGGING WRAPPER
# ───────────────────────────────────────────────────────────────
def wrapper_with_logging(fnc):
    def wrapper_log(X):
        logger.info(f"Starting step: {fnc.__name__}")
        start = time.time()
        try:
            result = fnc(X)
            elapsed = time.time() - start
            logger.info(f"Completed {fnc.__name__} in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Error in {fnc.__name__} after {elapsed:.3f}s: {e}", exc_info=True)
            raise
    return wrapper_log

# ───────────────────────────────────────────────────────────────
# FINAL PIPELINE (Option 2 — Modular Transcription)
# ───────────────────────────────────────────────────────────────
Pipeline = SKPipeline([
    ('check_ffmpeg', FunctionTransformer(wrapper_with_logging(check_ffmpeg_wrapper))),
    ('convert_audio', FunctionTransformer(wrapper_with_logging(convert_to_wav_wrapper))),
    ('transcribe_audio', FunctionTransformer(wrapper_with_logging(transcribe_wav_wrapper))),
    ('correct_transcription', FunctionTransformer(wrapper_with_logging(correct_txt_wrapper))),
    ('question_flag', FunctionTransformer(wrapper_with_logging(add_question_flag))),
    ('add_words', FunctionTransformer(wrapper_with_logging(add_num_words))),
    ('add_chars', FunctionTransformer(wrapper_with_logging(add_text_size_chars))),
    ('add_speech', FunctionTransformer(wrapper_with_logging(add_speech_rate))),
    ('add_speaker_turn', FunctionTransformer(wrapper_with_logging(add_speaker_turn_id))),
    ('save_data', FunctionTransformer(wrapper_with_logging(enriched_dt_wrapper))),
    ('check_dtype', FunctionTransformer(wrapper_with_logging(get_dtype_checks_wrapper))),
    ('check_csv', FunctionTransformer(wrapper_with_logging(csv_checks_wrapper))),
    ('check_timestamp', FunctionTransformer(wrapper_with_logging(get_timestamp_checks_wrapper))),
    ('total_words', FunctionTransformer(wrapper_with_logging(total_words_num))),
    ('speaker_most', FunctionTransformer(wrapper_with_logging(ml_speaker_rec_wrapper))),
    ('speaker_time', FunctionTransformer(wrapper_with_logging(ml_speaker_t_wrapper))),
    ('generate_report', FunctionTransformer(wrapper_with_logging(generate_report_csv_wrapper)))
])

# ───────────────────────────────────────────────────────────────
# RUN PIPELINE
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Running pipeline...")
    result = Pipeline.fit_transform("start")
    logger.info("Pipeline completed.")