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
MODEL_PATH     = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15")
OUTPUT_CSV     = os.path.join(BASE_DIR, "data", "transcriptions.csv")
CHUNK_SIZE     = 4000
# ─────────────────────────────────────────────────────────────────────────────

def parse_filename(filename):
    """
    Extracts speaker and version from filenames like:
      RATML-ANIKA-VN1.m4a
      RATML-DECLAN-VN3.m4a.m4a   ← double extension handled
    Returns (speaker, version) or (None, None) if pattern doesn't match.
    """
    # Strip all extensions (handles .m4a and .m4a.m4a)
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
        version = parts[2]          # e.g. "VN1"
        return speaker, version

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
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def transcribe_wav(wav_path, model):
    """Transcribes a WAV file using VOSK and returns the full transcript string."""
    with wave.open(wav_path, "rb") as wf:
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(False)

        parts = []
        while True:
            data = wf.readframes(CHUNK_SIZE)
            if not data:
                break
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "")
                if text:
                    parts.append(text)

        # Flush any remaining audio
        final = json.loads(rec.FinalResult()).get("text", "")
        if final:
            parts.append(final)

    return " ".join(parts).strip()


def main():
    print(f"Loading VOSK model from: {MODEL_PATH}")
    model = Model(MODEL_PATH)

    # Collect all m4a files (handles both .m4a and .m4a.m4a)
    all_files = sorted([
        f for f in os.listdir(RECORDINGS_DIR)
        if ".m4a" in f.lower()
    ])

    print(f"Found {len(all_files)} recording(s). Starting transcription...\n")

    rows = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for filename in all_files:
            m4a_path = os.path.join(RECORDINGS_DIR, filename)
            speaker, version = parse_filename(filename)

            if not speaker:
                print(f"  [SKIP] Could not parse filename: {filename}")
                continue

            print(f"  Processing: {filename}  →  Speaker={speaker}, Version={version}")

            # Convert to WAV
            tmp_wav = os.path.join(tmpdir, f"{speaker}_{version}.wav")
            if not convert_to_wav(m4a_path, tmp_wav):
                print(f"    [ERROR] ffmpeg conversion failed for {filename}")
                rows.append({
                    "filename": filename,
                    "speaker":  speaker,
                    "version":  version,
                    "transcript": "ERROR: conversion failed"
                })
                continue

            # Transcribe
            transcript = transcribe_wav(tmp_wav, model)
            print(f"    Transcript: {transcript[:80]}{'...' if len(transcript) > 80 else ''}")

            rows.append({
                "filename":   filename,
                "speaker":    speaker,
                "version":    version,
                "transcript": transcript
            })

    # Write CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "speaker", "version", "transcript"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Done! CSV saved to: {OUTPUT_CSV}")
    print(f"   {len(rows)} row(s) written.")


if __name__ == "__main__":
    main()