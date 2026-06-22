import os
import wave
import json
import csv
import subprocess
import tempfile
import time #added in to capture the time taken for each transcription
from datetime import datetime, timedelta  # added datetime and timedelta for timestamp generation
from vosk import Model, KaldiRecognizer

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
RECORDINGS_DIR = os.path.join(BASE_DIR, "data", "recordings")
MODEL_NAME     = "vosk-model-small-en-us-0.15"  # auto-downloaded and cached by Vosk on first run
OUTPUT_CSV     = os.path.join(BASE_DIR, "data", "transcriptions_V15.csv")
METRICS_CSV     = os.path.join(BASE_DIR, "data", "metrics_V15.csv")  #captures the time taken for each transcription and accuracy metrics
REFERENCE_CSV   = os.path.join(BASE_DIR, "data", "Correct_transcription.txt")   # correct transcripts for WER comparison
CHUNK_SIZE     = 4000
BASE_TIMESTAMP  = datetime(2026, 6, 18, 18, 0, 0)  # ← CHANGED: base timestamp for index=1 row (2026-04-28T10:00:00)
# ─────────────────────────────────────────────────────────────────────────────


def check_ffmpeg():
    """
    Validates that ffmpeg is installed and accessible on PATH.
    Exits early with a clear message if it is not found, rather than
    letting the code fail silently later during conversion.
    """
    result = subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode != 0:
        raise EnvironmentError(
            "ffmpeg was not found on your PATH.\n"
            "Please install it and ensure it is accessible before running this script.\n"
            "See the README for installation instructions."
        )


def parse_filename(filename):
    """
    Extracts speaker and index from filenames like:
      VN1-RATML-DANNY.m4a
      VN4-RATML-DECLAN.m4a
    Returns (speaker, index) or (None, None) if pattern doesn't match.
    """
    # Strip all extensions to have index number and speaker name.
    base = filename
    while True:
        root, ext = os.path.splitext(base)
        if not ext:
            break
        base = root

    # Expected format: VN{N}-RATML-{SPEAKER}
    parts = base.split("-")
    if len(parts) == 3 and parts[0].startswith("VN") and parts[1] == "RATML":
        index   = parts[0][2:]  # strips "VN" prefix e.g. "VN1" → "1"
        speaker = parts[2]      # e.g. "DANNY"
        return speaker, index

    return None, None


def convert_to_wav(m4a_path, tmp_wav_path):
    """Converts m4a to 16kHz mono 16-bit WAV using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",             # overwrite output if exists
        "-i", m4a_path,
        "-ar", "16000",             # sample rate
        "-ac", "1",                 # mono
        "-sample_fmt", "s16",       # 16-bit
        tmp_wav_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #discard ffmpeg normal output, error messages and warnings will not be shown in the console
    return result.returncode == 0 # True if conversion succeeded, False otherwise


def get_wav_duration(wav_path):
    """
    Returns the duration of a WAV file in seconds.
    Calculated by dividing the total number of audio frames
    by the sample rate of the file.
    """
    with wave.open(wav_path, "rb") as wf:
        frames = wf.getnframes()
        rate   = wf.getframerate()
        return round(frames / rate, 4)
    
def transcribe_wav(wav_path, model):
    """Transcribes a WAV file using VOSK and returns the full transcript string.
    
    SetWords(True) is enabled here so that VOSK returns per-word confidence
    scores alongside the transcript text. These are averaged to give an overall
    confidence score for each recording, indicating how certain VOSK was about
    its own output — lower scores highlight recordings it likely struggled with.
 
    Returns:
        transcript      (str):   the full transcribed text
        avg_confidence  (float): average per-word confidence score (0.0 – 1.0)
        word_count      (int):   total number of words transcribed
    """

    parts       = []
    confidences = []
 
    with wave.open(wav_path, "rb") as wf:
        # Initialise the recogniser with the Vosk language model loaded earlier and the WAV file's sample rate -16000 HZ in our case
        rec = KaldiRecognizer(model, wf.getframerate()) #  recogniser needs to know how many audio samples per second it should expect
        rec.SetWords(True) #if True, each word in the transcript will have a start and end timestamp. Setting to False gives us just the plain text.

       
        while True:
            data = wf.readframes(CHUNK_SIZE) #read a chunk of audio data from the WAV file. The size of each chunk is determined by CHUNK_SIZE, which is set to a recommended size of 4000 frames. 
            if not data: # checks whether any data was actually returned. Once the end of the file is reached, break exits the loop
                break
            # Feed the audio chunk to the recogniser; returns True when a
            # complete utterance boundary is detected and a result is ready - else it returns False, indicating that more audio is needed to complete the current utterance.
            if rec.AcceptWaveform(data):
        
                result = json.loads(rec.Result())        # as dict ->retrieves the transcribed text for that chunk. 
                text   = result.get("text", "")          # extract text string
                if text:
                    parts.append(text)
                for word_info in result.get("result", []):
                    confidences.append(word_info.get("conf", 0.0))# Extract the confidence score for each word in this chunk              
                

        # Flush any audio buffered after the last utterance boundary
        final_result = json.loads(rec.FinalResult()) #changed to dictionary from original build
        final_text   = final_result.get("text", "")   # extract text string
        if final_text:
            parts.append(final_text)

        # Extract confidence scores from the final chunk
        for word_info in final_result.get("result", []):
            confidences.append(word_info.get("conf", 0.0))

    transcript     = " ".join(parts).strip()
    word_count     = len(transcript.split()) if transcript else 0
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0 #A score close to 1.0 means Vosk was very certain — no other word was a plausible alternative and a score close to 0-> several other possible words scored nearly as well
 
    return transcript, avg_confidence, word_count

def compute_wer(reference, hypothesis):
    """
    Computes Word Error Rate (WER) between a reference (correct) transcript
    and the hypothesis (VOSK output).
 
    WER is calculated using edit distance — the minimum number of word-level
    insertions, deletions, and substitutions needed to turn the hypothesis
    into the reference, divided by the total number of reference words.

    WER is expressed as a ratio relative to the reference length:
        - 0.0  = perfect match, no errors
        - 0.5  = half the reference words were incorrect
        - 1.0  = every reference word was wrong
        - >1.0 = VOSK inserted more extra words than the reference contains
        e.g. reference has 2 words, VOSK output has 18 words →
        edit distance could be 17, giving WER = 8.5 - 
 
    Args:
        reference  (str): the correct transcript
        hypothesis (str): the VOSK-generated transcript
 
    Returns:
        float: WER score rounded to 4 decimal places
    """
    #Normalise and split both transcripts into word lists
    ref = reference.lower().split() #using lowercase in order to compare words only and not use of capital letters
    hyp = hypothesis.lower().split()
 
    # Build an edit distance matrix
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)] #Create an empty matrix filled with zeros
    for i in range(len(ref) + 1): #This answers: "how many edits to match the first i reference words against an empty hypothesis?"  
        d[i][0] = i # Fill first column: cost of deleting each reference word to match empty hypothesis
    for j in range(len(hyp) + 1): #"how many edits to match an empty reference against the first j hypothesis words?" 
        d[0][j] = j # Fill first row: cost of inserting each hypothesis word to match empty reference
 
    for i in range(1, len(ref) + 1): #This loops through every remaining cell and decides its cost based on whether the current pair of words match:
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])
    
    #WER = (Substitutions + Deletions + Insertions) / Number of reference words
    #The edit distance matrix gives the total number of edits (S+D+I) in the bottom-right cell, divided by len(ref).
    return round(d[len(ref)][len(hyp)] / max(len(ref), 1), 4) 
 
 
def load_reference_transcripts(reference_csv):
    """
    Loads ground-truth transcripts keyed by (index, speaker) for WER lookup.
    Speaker is normalised to lowercase to match against uppercase filenames.
    """
    references = {}
    if not os.path.exists(reference_csv):
        print(f"  [WARNING] No reference CSV found at {reference_csv} — WER will be skipped.")
        return references

    with open(reference_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["index"].strip(), row["speaker"].strip().lower())
            references[key] = row["transcript"].strip()

    print(f"  Loaded {len(references)} reference transcript(s) for WER comparison.\n")
    return references
 

def main():
    total_start = time.time()
 
    check_ffmpeg()
 
    print(f"Loading VOSK model: {MODEL_NAME}")
    model = Model(model_name=MODEL_NAME)
 
    references = load_reference_transcripts(REFERENCE_CSV)
 
    all_files = sorted([
        f for f in os.listdir(RECORDINGS_DIR)
        if ".m4a" in f.lower()
    ])
 
    print(f"Found {len(all_files)} recording(s). Starting transcription...\n")
 
    rows         = []
    metrics_rows = []
 
    with tempfile.TemporaryDirectory() as tmpdir:
        for filename in all_files:
            m4a_path       = os.path.join(RECORDINGS_DIR, filename)
            speaker, index = parse_filename(filename)
 
            if not speaker:
                print(f"  [SKIP] Could not parse filename: {filename}")
                continue
 
            print(f"  Processing: {filename}  →  Speaker={speaker}, Index={index}")
 
            tmp_wav = os.path.join(tmpdir, f"{speaker}_{index}.wav")
            if not convert_to_wav(m4a_path, tmp_wav):
                print(f"    [ERROR] ffmpeg conversion failed for {filename}")
                rows.append({
                    "filename":      filename,
                    "timestamp":     "",         
                    "index":         index,
                    "speaker":          speaker,     
                    "transcript":    "ERROR: conversion failed",
                    "time_taken_sec": ""          
                })
                continue
 
            recording_length_s = get_wav_duration(tmp_wav)
 
            file_start = time.time()
            transcript, avg_confidence, word_count = transcribe_wav(tmp_wav, model)
            file_duration = round(time.time() - file_start, 4)
 
            rtf              = round(file_duration / recording_length_s, 4) if recording_length_s > 0 else 0.0
            words_per_second = round(word_count / file_duration, 4) if file_duration > 0 else 0.0
 
            ref_key = (index, speaker.lower())
            wer = None
            if ref_key in references:
                wer = compute_wer(references[ref_key], transcript)
            else:
                print(f"    [WARNING] No reference found for index={index}, speaker={speaker}")
 
            print(f"    Transcript:  {transcript[:80]}{'...' if len(transcript) > 80 else ''}")
            print(f"    Confidence:  {avg_confidence}  |  Words: {word_count}  |  Time: {file_duration}s  |  WPS: {words_per_second}  |  WER: {wer}")
 
            rows.append({
                "filename":       filename,
                "timestamp":      "",             
                "index":          index,
                "speaker":           speaker,        
                "transcript":     transcript,
                "time_taken_sec": recording_length_s   
            })
 
            metrics_rows.append({
                "filename":           filename,
                "speaker":            speaker,
                "index":              index,
                "model":              MODEL_NAME,
                "recording_length_s": recording_length_s,
                "duration_s":         file_duration,
                "rtf":                rtf,
                "word_count":         word_count,
                "words_per_sec":      words_per_second,
                "avg_confidence":     avg_confidence,
                "wer":                wer if wer is not None else "N/A"
            })
 
    total_duration = round(time.time() - total_start, 4)
    print(f"\n  Total runtime: {total_duration}s")
 
    # ── Sort both lists by index ascending ────────────────────────────────────
    rows.sort(key=lambda r: int(r["index"]) if str(r["index"]).isdigit() else 0)  #sort rows (not just metrics) by index
    metrics_rows.sort(key=lambda r: int(r["index"]))
 
    # ── Generate timestamps ───────────────────────────────────────────────────
    # The first row (index=1) receives BASE_TIMESTAMP.                           new timestamp generation block
    # Each subsequent row's timestamp = previous timestamp + that row's
    # time_taken_sec, representing when that speaker began talking relative
    # to the start of the meeting.
    current_timestamp = BASE_TIMESTAMP                                           
    for row in rows:                                                             
        row["timestamp"] = current_timestamp.strftime("%Y-%m-%dT%H:%M:%S")     #format as ISO 8601
        if isinstance(row["time_taken_sec"], float):                             
            current_timestamp += timedelta(seconds=row["time_taken_sec"])       #  advance clock by the recording length
            
    # ── Write transcriptions CSV ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[                                 
            "filename", "timestamp", "index", "speaker", "transcript", "time_taken_sec"
        ])
        writer.writeheader()
        writer.writerows(rows)
 
    # ── Write metrics CSV ─────────────────────────────────────────────────────
    with open(METRICS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "speaker", "index", "model",
            "recording_length_s", "duration_s", "rtf",
            "word_count", "words_per_sec", "avg_confidence", "wer"
        ])
        writer.writeheader()
        writer.writerows(metrics_rows)
        writer.writerow({
            "filename":       "TOTAL",
            "speaker":        "",
            "index":          "",
            "model":          MODEL_NAME,
            "duration_s":     total_duration,
            "word_count":     sum(r["word_count"] for r in metrics_rows),
            "words_per_sec":  "",
            "avg_confidence": "",
            "wer":            ""
        })
 
    print(f"\n✅ Done!")
    print(f"   Transcriptions → {OUTPUT_CSV}  ({len(rows)} row(s))")
    print(f"   Metrics        → {METRICS_CSV}")
 
 
if __name__ == "__main__":
    main()