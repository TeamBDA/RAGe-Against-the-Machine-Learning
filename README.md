# BDA-Team: RAGe Against the Machine Learning
<h2>Big Data Analytics (BDA) team project repository</h2>

<h3>A project pipeline built with the following</h3>

* Takes in short spoken recordings (.m4a filetype) as input.
* Transcribes the recorded speech with a Vosk audio model.
* Corrects the transcript with Gemini 3.1 flash-lite.
* Saves the results in a CSV dataset.
* Enriches the transcriptions with Python, including:
  * Question flag (whether or not the recording includes a question).
  * Number of words spoken.
  * Number of characters in transcripts.
  * Speech rate.
  * Speaker turn ID.
* Validates the dataset before analysis.
* Produces basic metrics for transcriptions.

---

<h3>Instructions:</h3>
This software allows you to transcribe a directory of recordings. 
<b>Pre-Requisites:</b>

 * Python (to run software)
 * FFMPEG (for audio processing)
 * Gemini API key (for transcription cleaning)
 * Installed python dependencies listed in requirements.txt

<b>Setup:</b>

 * Install Python:  `https://www.python.org/downloads/`
 * InstalL FFMPEG: `https://ffmpeg.org/download.html`
 * Start virtual environment: `python -m venv .venv-RAGe`
 * Activate virtual environment: `source .venv-RAGe/Scripts/activate`
 * Install dependencies: `pip install -r requirements.txt`

<b>To run software (from top level of repo):</b>

Using defaults:
```
python src/main.py
```

Specifying a bespoke directory for your recordings (defaults to 'data/recordings'):
```
python src/main.py -d "path/to/recordings/folder"
```

Specifying a bespoke path for your ffmpeg (defaults to use $PATH for "ffmpeg"):
```
python src/main.py -f "path/to/your/ffmpeg.exe"
```

After running `main.py`, you will be prompted for your Gemini API key. This can be found here - `https://aistudio.google.com/api-keys`.

---

<h3>Time and Space Complexities</h3>

* Danny (enrich_transcriptions.py):
_N = Number of rows, L = length of row_
 * * load_data(file_path)
 Time Complexity: O(N x L)
 Space Complexity: O(N x L)
 * * add_question_flag(df)
 Time Complexity: O(N x L)
 Space Complexity: O(N)
 * * add_num_words(df)
 Time Complexity: O(N x L)
 Space Complexity: O(N)
 * * add_text_size_chars(df)
 Time Complexity: O(N)
 Space Complexity: O(N)
 * * add_speech_rate(df)
 Time Complexity: O(N)
 Space Complexity: O(N)
 * * add_speaker_turn_id(df)
 Time Complexity: O(N)
 Space Complexity: O(N)
 * * save_enriched_data(df, output_file)
 Time Complexity: O(N)
 Space Complexity: O(1)
---
* Kevin (vaildate_transcriptions.py):
_N = Number of rows, L = length of row_
 * * get_validation_msgs(success, message)
 Time Complexity: O(N)
 Space Complexity: O(N)
 * * log_error(table, msg)
 Time Complexity: O(1)
 Space Complexity: O(1)
 * * log_success(table, msg):
 Time Complexity: O(1)
 Space Complexity: O(1)
 * * get_dtype_checks(df, table, cols_int, col_bool)
 Time Complexity: O(NxL)
 Space Complexity: O(N)
 * * get_csv_checks(df, table)
 Time Complexity: O(N)
 Space Complexity: O(1)
 * * get_timestamp_checks(df, table, timestamp_col)
 Time Complexity: O(N)
 Space Complexity: O(1)
---
* Anton (calculate_metrics.py):
_N = Number of rows, L = length of row_ 
* * read_file(filename) 
Time Complexity: O(N) 
Space Complexity: O(N)
* * get_rows(data) 
Time Complexity: O(N) 
Space Complexity: O(N)
* * total_words_num(data) 
Time Complexity: O(NxL) 
Space Complexity: O(N)
* * ml_speaker_rec(data, mode) 
Time Complexity: O(NxL) 
Space Complexity: O(1)
* * ml_speaker_t(data, mode) 
Time Complexity: O(NxL) 
Space Complexity: O(N)
* * speakers_total_time(data) 
Time Complexity: O(N) 
Space Complexity: O(N)
* * meeting_total_time(data) 
Time Complexity: O(N) 
Space Complexity: O(1)
* * average_time_per_speaker(data) 
Time Complexity: O(N) 
Space Complexity: O(N)
* * average_time_per_meeting(data) 
Time Complexity: O(N) 
Space Complexity: O(N)
* * average_speech_rate(data) 
Time Complexity: O(NxL) 
Space Complexity: O(N)
* * questions_per_speaker(data) 
Time Complexity: O(N) 
Space Complexity: O(N)
* * generate_report_csv(data, output_filename) 
Time Complexity: O(NxL) 
Space Complexity: O(N)
* * run(df_or_filename) 
Time Complexity: O(NxL) 
Space Complexity: O(N)
---

<h3>Key Links</h3>
<br/>
BDA Team Channel (Teams): https://teams.microsoft.com/l/chat/19:af3dbf5b938d46369bf0065b384b6785@thread.v2/conversations?context=%7B%22contextType%22%3A%22chat%22%7D
<br/>
See link to Project Spec: https://github.com/warestack/bda/tree/main/team-project
<br/>
See the link to the BDA Teams form: https://forms.cloud.microsoft/pages/responsepage.aspx?id=R3_QiVjSPEaHAGNf-uyjjvXa34CVqJ9Nt0-aLae0jCxUQjhVU0RBNVpLUzhUTFVLUkRTSjVMUTRLRi4u&route=shorturl
<br/>
See link to Peer Review Form: https://github.com/warestack/bda/blob/main/team-project/Peer_Evaluation_Form.docx

VOSK speech software: <br/><br/>
VOSK Install: https://alphacephei.com/vosk/install
<br/>
VOSK model versions: https://alphacephei.com/vosk/models
