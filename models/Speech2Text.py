import os
import wave
import json
import csv
import subprocess
import tempfile
from vosk import Model, KaldiRecognizer

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
RECORDINGS_DIR = os.path.join(BASE_DIR, "data", "recordings")
MODEL_NAME     = "vosk-model-small-en-us-0.15"  # auto-downloaded and cached by Vosk on first run
OUTPUT_CSV     = os.path.join(BASE_DIR, "data", "transcriptions.csv")
CHUNK_SIZE     = 4000
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
      RATML-ANIKA-VN1.m4a
    Returns (speaker, index) or (None, None) if pattern doesn't match.
    """
    # Strip all extensions
    base = filename
    while True:
        root, ext = os.path.splitext(base)
        if not ext:
            break
        base = root

    # Expected format: RATML-{SPEAKER}-VN{N}
    parts = base.split("-")
    if len(parts) == 3 and parts[0] == "RATML" and parts[2].startswith("VN"):
        speaker = parts[1]
        index = parts[2]          # e.g. "VN1"
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


def transcribe_wav(wav_path, model):
    """Transcribes a WAV file using VOSK and returns the full transcript string."""
    with wave.open(wav_path, "rb") as wf:
        # Initialise the recogniser with the Vosk language model loaded earlier and the WAV file's sample rate -16000 HZ in our case
        rec = KaldiRecognizer(model, wf.getframerate()) #  recogniser needs to know how many audio samples per second it should expect
        rec.SetWords(False) #if True, each word in the transcript will have a start and end timestamp. Setting to False gives us just the plain text.

        parts = []
        while True:
            data = wf.readframes(CHUNK_SIZE) #read a chunk of audio data from the WAV file. The size of each chunk is determined by CHUNK_SIZE, which is set to a recommended size of 4000 frames. 
            if not data: # checks whether any data was actually returned. Once the end of the file is reached, break exits the loop
                break
            # Feed the audio chunk to the recogniser; returns True when a
            # complete utterance boundary is detected and a result is ready - else it returns False, indicating that more audio is needed to complete the current utterance.
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "") # retrieves the transcribed text for that chunk. Vosk returns its result as a JSON string
                if text:
                    parts.append(text)

        # Flush any audio buffered after the last utterance boundary
        final = json.loads(rec.FinalResult()).get("text", "")
        if final:
            parts.append(final)

    return " ".join(parts).strip()


def main():
    # Fail fast if ffmpeg is missing before we do any real work
    check_ffmpeg()

    print(f"Loading VOSK model: {MODEL_NAME}")
    model = Model(model_name=MODEL_NAME)

    # Collect all m4a files
    all_files = sorted([
        f for f in os.listdir(RECORDINGS_DIR)
        if ".m4a" in f.lower()
    ])

    print(f"Found {len(all_files)} recording(s). Starting transcription...\n")

    rows = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for filename in all_files:
            m4a_path = os.path.join(RECORDINGS_DIR, filename)
            speaker, index = parse_filename(filename)

            if not speaker:
                print(f"  [SKIP] Could not parse filename: {filename}")
                continue

            print(f"  Processing: {filename}  →  Speaker={speaker}, Index={index}")

            # Convert to WAV
            tmp_wav = os.path.join(tmpdir, f"{speaker}_{index}.wav")
            if not convert_to_wav(m4a_path, tmp_wav):
                print(f"    [ERROR] ffmpeg conversion failed for {filename}")
                rows.append({
                    "filename":   filename,
                    "speaker":    speaker,
                    "index":      index,
                    "transcript": "ERROR: conversion failed"
                })
                continue

            # Transcribe
            transcript = transcribe_wav(tmp_wav, model)
            print(f"    Transcript: {transcript[:80]}{'...' if len(transcript) > 80 else ''}")

            rows.append({
                "filename":   filename,
                "speaker":    speaker,
                "index":      index,
                "transcript": transcript
            })

    # Write CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "speaker", "index", "transcript"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Done! CSV saved to: {OUTPUT_CSV}")
    print(f"   {len(rows)} row(s) written.")


if __name__ == "__main__":
    main()