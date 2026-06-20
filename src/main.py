import datetime

import transcribe_recordings
import correct_transcriptions
import enrich_transcriptions
import validate_transcriptions
import calculate_metrics


def main():
    print("\n" + "=" * 62)
    print("  RAGe Against the Machine-Learning — Transcription Pipeline")
    print("=" * 62 + "\n")

    # Prompt for Gemini API key once, upfront
    api_key = input("Please enter your Google Gemini API key: ").strip()
    if not api_key:
        raise ValueError("A Gemini API key is required for the correction step.")

    # Step 1: Transcribe
    print("\n── Step 1/5: Transcribing recordings ──")
    df = transcribe_recordings.run()

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