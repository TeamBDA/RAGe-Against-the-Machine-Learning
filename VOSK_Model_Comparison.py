import os
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR      = os.path.join(BASE_DIR, "data")
METRICS_V15   = os.path.join(DATA_DIR, "metrics_V15.csv")
METRICS_V22   = os.path.join(DATA_DIR, "metrics_V22.csv")
OUTPUT_CSV    = os.path.join(DATA_DIR, "model_comparison.csv")

# Columns used in all comparisons
COMPARISON_COLS = ["wer", "avg_confidence", "words_per_sec", "rtf"]
# ─────────────────────────────────────────────────────────────────────────────


def load_metrics(filepath):
    """
    Loads a metrics CSV, drops the TOTAL summary row appended by Speech2Text,
    and ensures all numeric comparison columns are correctly typed.
    """
    df = pd.read_csv(filepath)
    # Drop the TOTAL row — it has no speaker and would skew averages
    df = df[df["speaker"].notna()].copy()
    # Cast comparison columns to numeric, changing any stray strings to NaN
    for col in COMPARISON_COLS + ["recording_length_s", "duration_s", "word_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def overall_comparison(v15, v22):
    """
    Builds a side-by-side summary table comparing the two models across
    the four key metrics, averaged across all recordings.

    Metrics:
        wer            — Word Error Rate (lower is better)
        avg_confidence — VOSK per-word confidence score (higher is better)
        words_per_sec  — Transcription throughput (higher = faster processing)
        rtf            — Real-Time Factor: VOSK runtime / recording length
                         (lower = faster than real-time)
    """
    rows = []
    metric_labels = {
        "wer":            "Avg Word Error Rate (WER)",
        "avg_confidence": "Avg Confidence Score",
        "words_per_sec":  "Avg Words Per Second",
        "rtf":            "Avg Real-Time Factor (RTF)",
    }

    for col, label in metric_labels.items():
        v15_mean = round(v15[col].mean(), 4)
        v22_mean = round(v22[col].mean(), 4)

        # Direction of improvement differs per metric
        if col in ("wer", "rtf"):
            # Lower is better — negative delta means V22 improved
            delta     = round(v22_mean - v15_mean, 4)
            direction = "V22 better" if delta < 0 else ("V15 better" if delta > 0 else "Equal")
        else:
            # Higher is better — positive delta means V22 improved
            delta     = round(v22_mean - v15_mean, 4)
            direction = "V22 better" if delta > 0 else ("V15 better" if delta < 0 else "Equal")

        rows.append({
            "Metric":          label,
            "V15":             v15_mean,
            "V22":             v22_mean,
            "Delta (V22-V15)": delta,
            "Winner":          direction,
        })

    return pd.DataFrame(rows)


def speaker_comparison(v15, v22):
    """
    Builds a per-speaker breakdown comparing the two models, showing each
    speaker's average across the four key metrics for both V15 and V22.
    The combined table is indexed by speaker for easy reading.
    """
    metrics_map = {
        "wer":            "WER",
        "avg_confidence": "Confidence",
        "words_per_sec":  "Words/Sec",
        "rtf":            "RTF",
    }

    # Aggregate per speaker for each model
    v15_speaker = v15.groupby("speaker")[COMPARISON_COLS].mean().round(4)
    v22_speaker = v22.groupby("speaker")[COMPARISON_COLS].mean().round(4)

    # Rename columns to include model suffix so they don't clash when merged
    v15_speaker.columns = [f"{metrics_map[c]}_V15" for c in COMPARISON_COLS]
    v22_speaker.columns = [f"{metrics_map[c]}_V22" for c in COMPARISON_COLS]

    # Merge on speaker index — inner join keeps only speakers present in both
    combined = v15_speaker.join(v22_speaker, how="inner")

    # Reorder columns so each metric's V15/V22 pair sits together
    ordered_cols = []
    for c, short in metrics_map.items():
        ordered_cols += [f"{short}_V15", f"{short}_V22"]
    combined = combined[ordered_cols]

    return combined


def combined_table(v15, v22):
    """
    Produces a flat row-per-recording table with both models' metrics
    side by side, keyed by filename and speaker. Useful for per-recording
    deep dives rather than aggregated averages.
    """
    # Tag each dataframe with its model version before merging
    v15_tagged = v15[["filename", "speaker", "index"] + COMPARISON_COLS].copy()
    v22_tagged = v22[["filename", "speaker", "index"] + COMPARISON_COLS].copy()

    v15_tagged.columns = ["filename", "speaker", "index"] + [f"{c}_V15" for c in COMPARISON_COLS]
    v22_tagged.columns = ["filename", "speaker", "index"] + [f"{c}_V22" for c in COMPARISON_COLS]

    merged = pd.merge(v15_tagged, v22_tagged, on=["filename", "speaker", "index"])
    merged = merged.sort_values("index").reset_index(drop=True)

    return merged


def print_section(title, df):
    """Prints a labelled section to the console with consistent formatting."""
    width = 72
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)
    print(df.to_string())
    print()


def main():
    print("Loading metrics files...")
    v15 = load_metrics(METRICS_V15)
    v22 = load_metrics(METRICS_V22)
    print(f"  V15: {len(v15)} recording(s) | V22: {len(v22)} recording(s)")

    # ── 1. Overall model comparison ───────────────────────────────────────────
    overall = overall_comparison(v15, v22)
    print_section("OVERALL MODEL COMPARISON — V15 vs V22", overall)

    # ── 2. Per-speaker comparison ─────────────────────────────────────────────
    speaker = speaker_comparison(v15, v22)
    print_section("PER-SPEAKER COMPARISON — Averages across all recordings", speaker)

    # ── 3. Per-recording combined table ───────────────────────────────────────
    combined = combined_table(v15, v22)
    print_section("PER-RECORDING COMBINED TABLE — All metrics side by side", combined)

    # ── Save all three tables to a single CSV ─────────────────────────────────
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write("OVERALL MODEL COMPARISON\n")
        overall.to_csv(f, index=False)
        f.write("\nPER-SPEAKER COMPARISON\n")
        speaker.to_csv(f)
        f.write("\nPER-RECORDING COMBINED TABLE\n")
        combined.to_csv(f, index=False)

    print(f"\n✅ Comparison saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()