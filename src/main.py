import argparse
import datetime
import os
import subprocess

import transcribe_recordings
import correct_transcriptions
import enrich_transcriptions
import validate_transcriptions
import calculate_metrics

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
RECORDINGS_DIR = os.path.join(BASE_DIR, "data", "recordings")


def check_ffmpeg(ffmpeg_path: str = "ffmpeg") -> None:
    """
    Validates that ffmpeg is installed and accessible on PATH.
    Exits early with a clear message if it is not found, rather than
    letting the code fail silently later during conversion.
    """
    result = subprocess.run(
        [ffmpeg_path, "-version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode != 0:
        raise EnvironmentError(
            "ffmpeg was not found on your PATH.\n"
            "Please install it and ensure it is accessible before running this script.\n"
            "See the README for installation instructions."
        )

def main():    
    parser = argparse.ArgumentParser(
        description="RAGe Against the Machine-Learning — Transcription Pipeline"
    )
    # Allow optional ffmpeg path (can be called with either -f or --ffmpeg)
    parser.add_argument(
        "-f", "--ffmpeg",
        type=str,
        default="ffmpeg",
        help="Optional: Path to the ffmpeg executable."
    )

    # Allow optional recordings dir flag (can be called with either -d or --dir)
    parser.add_argument(
        "-d", "--dir",
        type=str,
        default=RECORDINGS_DIR,
        help="Optional: Path to an alternative directory containing .m4a recordings."
    )

    args = parser.parse_args()

    # Check ffmpeg availability before proceeding with the pipeline
    check_ffmpeg(ffmpeg_path=args.ffmpeg)

    # Collect all m4a files
    recordings = sorted([
        f for f in os.listdir(args.dir)
        if ".m4a" in f.lower()
    ])

    if not recordings:
        raise FileNotFoundError(
            f"No .m4a recordings found in directory: {args.dir}\n"
            "Please ensure you have recordings to transcribe."
        )

    print("\n" + "=" * 62)
    print("  RAGe Against the Machine-Learning — Transcription Pipeline")
    print("=" * 62 + "\n")

    # Prompt for Gemini API key once, upfront
    api_key = input("Please enter your Google Gemini API key: ").strip()
    if not api_key:
        raise ValueError("A Gemini API key is required for the correction step.")

    # Step 1: Transcribe
    print("\n── Step 1/5: Transcribing recordings ──")
    df = transcribe_recordings.run(recordings_dir=args.dir, recordings=recordings)

    # Step 2: Correct
    print("\n── Step 2/5: Correcting transcriptions ──")
    df = correct_transcriptions.run(df, api_key=api_key)

    # Step 3: Enrich → saves enriched_transcripts.csv
    print("\n── Step 3/5: Enriching transcriptions ──")
    df = enrich_transcriptions.run(df)

    # Step 4: Validate → saves error_report_<date>.docx
    print("\n── Step 4/5: Validating transcriptions ──")
    validate_transcriptions.run()

    # Step 5: Metrics → saves metrics_report.csv
    print("\n── Step 5/5: Calculating metrics ──")
    calculate_metrics.run(df)

    print("\n" + "=" * 62)
    print("  ✅ Pipeline complete. Outputs written:")
    print("    • data/results/enriched_transcripts.csv")
    print(f"    • documents/error_report_{datetime.date.today()}.docx")
    print("    • data/results/metrics_report.csv")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()