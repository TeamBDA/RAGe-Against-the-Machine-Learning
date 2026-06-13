import os
import pandas as pd
import datetime
from docx import Document

# ── Project Path Setup ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "documents")
REPORT_FILE = os.path.join(REPORT_DIR, f"csvreport_{datetime.date.today()}.docx")
CSV_FILE = os.path.join(TRANSCRIPTIONS_DIR, "transcriptions - vosk_0.22-lgraph.csv")


def get_validation_msgs(success, message):
    status = "VALIDATION SUCCESS" if success else "VALIDATION FAILED"
    fullmsg = f"[{status}] {message}"
    print(fullmsg)
    return fullmsg


def get_dtype_checks(df, table):
    """Vectorised Data type validation logic using Pandas operations."""
    cols_int = ['num_words', 'speech_rate_wps', 'speaker_turn_id']
    col_bool = 'question_flag'

    # 1. Numeric validation (Vectorised)
    for col in cols_int:
        if col not in df.columns:
            continue
        
        # Coerce to numeric, making mistakes NaN
        numeric_col = pd.to_numeric(df[col], errors='coerce')
        
        # Find missing or non-positive numbers
        invalid_mask = numeric_col.isna() | (numeric_col <= 0)
        invalid_rows = df[invalid_mask]

        for idx, row in invalid_rows.iterrows():
            current_row = idx + 2
            msg = f"Invalid or non-positive integer/float at row {current_row}, column {col}"
            fullmsg = get_validation_msgs(False, msg)
            table.add_row().cells[0].text = fullmsg

    # 2. Boolean Validation (Vectorised)
    if col_bool in df.columns:
        # Standardise strings to lower case to validate values
        s_vals = df[col_bool].astype(str).str.strip().str.lower()
        
        valid_true = s_vals.isin(["true", "1", "yes", "1.0"])
        valid_false = s_vals.isin(["false", "0", "no", "0.0"])
        invalid_mask = ~(valid_true | valid_false)
        
        # Update original dataframe to real booleans
        df.loc[valid_true, col_bool] = True
        df.loc[valid_false, col_bool] = False
        
        # Document any validation errors
        for idx in df[invalid_mask].index:
            msg = f"Invalid boolean '{df.loc[idx, col_bool]}' at row {idx + 2}, column {col_bool}"
            fullmsg = get_validation_msgs(False, msg)
            table.add_row().cells[0].text = fullmsg


def get_csv_checks(df, table):
    """Validates CSV structure using vectorised checks."""
    # Strip spaces from string entries efficiently
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # Find indices of empty cells
    empty_rows, empty_cols = pd.isna(df).to_numpy().nonzero()
    for row, col in zip(empty_rows, empty_cols):
        msg = f"Empty cell found at CSV line {row + 2}, Column index: {col}"
        fullmsg = get_validation_msgs(False, msg)
        table.add_row().cells[0].text = fullmsg

    rowlength = len(df)
    if rowlength >= 25:
        msg = f"Row count ({rowlength}) is valid (25 or more)."
        fullmsg = get_validation_msgs(True, msg)
        table.add_row().cells[0].text = fullmsg
    else:
        msg = f"Row count ({rowlength}) is below the minimum required (25)."
        fullmsg = get_validation_msgs(False, msg)
        table.add_row().cells[0].text = fullmsg

    return rowlength


def get_timestamp_checks(df, table):
    """Timestamp validation logic."""
    if 'timestamp' not in df.columns:
        fullmsg = get_validation_msgs(False, "A timestamp column could not be found.")
        table.add_row().cells[0].text = fullmsg
        return

    # Try casting to datetime smoothly across the whole column
    parsed_timestamps = pd.to_datetime(df['timestamp'], format="mixed", errors="coerce")
    invalid_ts = df[parsed_timestamps.isna()]

    if not invalid_ts.empty:
        for idx in invalid_ts.index:
            msg = f"Timestamp validation failed at row {idx + 2} value: '{df.loc[idx, 'timestamp']}'"
            fullmsg = get_validation_msgs(False, msg)
            table.add_row().cells[0].text = fullmsg
        return

    print("All timestamps are valid.")


if __name__ == "__main__":
    reportdoc = Document()
    reportdoc.add_heading(f"Validation Checks Report \n File: {CSV_FILE}")

    table = reportdoc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Error Description"

    # Read the file once with standard baseline settings
    try:
        df = pd.read_csv(CSV_FILE, skip_blank_lines=True, na_values=["", " ", "  "])
        
        # Execute validation pipeline linearly
        get_csv_checks(df, table)
        get_dtype_checks(df, table)
        get_timestamp_checks(df, table)
        
    except FileNotFoundError:
        print(f"[CRITICAL] File not found at target directory: {CSV_FILE}")
    except Exception as e:
        print(f"[CRITICAL] Uncaught pipeline execution error: {str(e)}")

    # Save out report safely
    os.makedirs(REPORT_DIR, exist_ok=True)
    reportdoc.save(REPORT_FILE)
    print(f"Report successfully written to {REPORT_FILE}")