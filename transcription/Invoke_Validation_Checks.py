# ── Info for error handling and validation check functions──────────────────────────────────────────────────────
#Use try/catch (Err Ex handling)
#Step: Get CSV and check rows/cols:
#Before analytics, your code should check that the final CSV is usable (the CSV has at least 25 rows).
#At minimum, check:
#No required values are missing.
#data type validation checks
#num_words is numeric and greater than 0.
#speech_rate_wps is numeric and greater than 0.
#question_flag contains boolean values.
#speaker_turn_id is numeric and greater than 0.
#Step:
#Row 4: timestamp "-04-28T10:00:05" is not a valid datetime.
#timestamp values can be parsed as dates/times.
#Step:
#Row 3: speech_rate_wps is missing
#Step:
#Validation should print clear messages. For example:
#Validation failed/Validation check completed successfully
# ── END Info for error handling and validation check functions──────────────────────────────────────────────────────
import os
import csv
from turtledemo.clock import current_day
import pandas as pd
import datetime
from docx import Document, table

# ── Project Path Setup ────────────────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR         = os.path.join(BASE_DIR, "documents")
REPORT_FILE        = os.path.join(REPORT_DIR, f"csvreport_{datetime.date.today()}.docx")
CSV_FILE           = os.path.join(TRANSCRIPTIONS_DIR, "transcriptions - vosk_0.15.csv")

# ── Info for error handling and validation check functions─────────────────────────────
# Define a CSV dictionary to re-use for col names
csvdict={
         'words':'num_words',
         'speechrate':'speech_rate_wps',
         'speakerid':'speaker_turn_id',
         'question':'question_flag'
}

"""Generates report from CSV file."""
# Create a docx (Word) doc for reporting
reportdoc = Document()
reportdoc.add_heading(f"Validation Check Report for file {datetime.date.today()}", level=1)
# Create a table with 1 header and all rows and columns
table       = reportdoc.add_table(rows=1, cols=1)
table.style = "Table Grid"
hdr         = table.rows[0].cells
hdr[0].text = "Error Description"

def get_validation_msgs(success, message):
    """Prints a structured validation message."""
    status = "VALIDATION SUCCESS" if success else "VALIDATION FAILED"
    fullmsg= f"[{status}] {message}"
    print(fullmsg)
    return fullmsg

def get_dtype_checks(csv_file):
    """Data type validation logic."""
    # Arr to collect all errors
    errors      = []
    current_col = None
    current_row = None

    try:
        # Load CSV normally (no converters)
        readcsv = pd.read_csv(
            csv_file,
            usecols=[csvdict["words"], csvdict['speechrate'], csvdict['speakerid'], csvdict['question']],
            header=0
        )

        cols_int = ['num_words', 'speech_rate_wps', 'speaker_turn_id']
        col_bool = 'question_flag'

        # Add filename to report
        row               = table.add_row()
        row.cells[0].text = csv_file

        # Integer validation
        for col in cols_int:
            current_col = col
            for idx, val in readcsv[col].items():
                current_row = idx + 2  # +2 for header row

                sval = str(val).strip()
                if sval == "":
                    msg               = f"Invalid integer at row {current_row}, column {col}"
                    fullmsg           = get_validation_msgs(False, msg)
                    errors.append(fullmsg)
                    row               = table.add_row()
                    row.cells[0].text = fullmsg

                    continue
                try:
                    ival = int(sval)
                except:
                    msg               = f"Invalid integer at row {current_row}, column {col}"
                    fullmsg           = get_validation_msgs(False, msg)
                    errors.append(fullmsg)
                    row               = table.add_row()
                    row.cells[0].text = fullmsg
                    continue

                if ival <= 0:
                    print(f"[INVALID] Row {current_row}: {col} must be > 0 → '{ival}'")
                else:
                    print(f"[OK] Row {current_row}: {col} = {ival}")

        # Boolean validation
        validated_bools = []  # store validated values separately
        current_col     = col_bool
        for idx, val in readcsv[col_bool].items():
            current_row = idx + 2

            sval = str(val).strip().lower()
            if sval in ("true", "1", "yes"):
                validated_bools.append(True)
                continue
            elif sval in ("false", "0", "no"):
                validated_bools.append(False)
                continue
            else:
                msg               = f"Invalid boolean '{val}' at row {current_row}, column {col_bool}"
                fullmsg           = get_validation_msgs(False, msg)
                errors.append(fullmsg)
                row               = table.add_row()
                row.cells[0].text = fullmsg
                validated_bools.append(None)
                continue
            print(f"[OK] Row {current_row}: question_flag = {bval}")

            # Replace string with real bool
            readcsv.at[idx, col_bool] = bval

        if errors:
            #join all errs into 1 unified msg output
            msg               = "\n[VALIDATION FAILED] Data validation failed:\n"+ "\n".join(errors)
            fullmsg           = get_validation_msgs(False, msg)
            errors.append(fullmsg)
            row               = table.add_row()
            row.cells[0].text = fullmsg

        else:
            print("\n[VALIDATION SUCCESS] Data validation passed.")
            print(readcsv.dtypes)

        print("\n[VALIDATION SUCCESS] All data types are correct.")
        print(readcsv.dtypes)

    except Exception as e:
        msg = f"Validation error: {e}"
        if current_col is not None:
            msg += f" (column={current_col}"
            if current_row is not None:
                msg += f", row={current_row}"
            msg += ")"
        fullmsg           = get_validation_msgs(False, msg)
        errors.append(fullmsg)
        row               = table.add_row()
        row.cells[0].text = fullmsg

def get_csv_checks(csv_file):
    """Validates CSV structure, empties, and row count."""
    rowlength = None
    empties_found = False

    try:
        readcsv = pd.read_csv(
            csv_file,
            header=0,
            skip_blank_lines=True,
            na_values=["", " ", "  "]
        )

        readcsv = readcsv.apply(
            lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x)
        )

        empty_cells = pd.isna(readcsv)
        row_indices, col_indices = empty_cells.to_numpy().nonzero()

        if len(row_indices) > 0:
            empties_found = True
            for row, col in zip(row_indices, col_indices):
                print(f"Empty cell found at CSV line {row + 2}, Column index: {col}")
        else:
            print("There are no empty columns or cells in the CSV file.")

        rowlength = len(readcsv)
        print(f"There are {rowlength} data rows in the CSV file.")

        if rowlength >= 25:
            msg               = f"Row count ({rowlength}) is valid (25 or more)."
            fullmsg           = get_validation_msgs(True, msg)
            row               = table.add_row()
            row.cells[0].text = fullmsg
        else:
            msg               = f"Row count ({rowlength}) is below the minimum required (25)."
            fullmsg           = get_validation_msgs(False, msg)
            row               = table.add_row()
            row.cells[0].text = fullmsg

    except pd.errors.EmptyDataError:
        msg                   = "The CSV file is empty or has a malformed header."
        fullmsg               = get_validation_msgs(False, msg)
        row                   = table.add_row()
        row.cells[0].text     = fullmsg
    except FileNotFoundError:
        msg                   =  f"File not found at: {csv_file}"
        fullmsg               = get_validation_msgs(False, msg)
        row                   = table.add_row()
        row.cells[0].text     = fullmsg
    except Exception as e:
        msg                   = f"An unexpected parsing error occurred: {str(e)}"
        fullmsg               = get_validation_msgs(False, msg)
        row                   = table.add_row()
        row.cells[0].text     = fullmsg
    return rowlength


def get_timestamp_checks(csv_file):
    """Timestamp validation logic."""
    try:
        readcsv = pd.read_csv(csv_file, header=0)
        idx = 0

        if 'timestamp' not in readcsv.columns:
            msg               =  f"A timestamp column could not be found at row {idx}"
            fullmsg           = get_validation_msgs(False, msg)
            row               = table.add_row()
            row.cells[0].text = fullmsg
            return

        readcsv['timestamp'] = pd.to_datetime(
            readcsv['timestamp'],
            format="mixed",
            errors="coerce"
        )

        invalid_ts = readcsv[readcsv['timestamp'].isna()]

        if not invalid_ts.empty:
            for idx in invalid_ts.index:
                print(f"[INVALID] Row {idx + 2}: timestamp → '{readcsv.loc[idx, 'timestamp']}'")
            msg               =  "Timestamp validation failed."
            fullmsg           = get_validation_msgs(False, msg)
            row               = table.add_row()
            row.cells[0].text = fullmsg
            return

        print("All timestamps are valid.")
        print(readcsv['timestamp'])

        dttimeobj = readcsv['timestamp'].iloc[0]
        formatted = dttimeobj.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Timestamp value {formatted}")

    except pd.errors.EmptyDataError:
        msg               = "The CSV file is empty."
        fullmsg           = get_validation_msgs(False, msg)
        row               = table.add_row()
        row.cells[0].text = fullmsg
    except Exception as e:
        msg               = f"Timestamp validation error: {str(e)}"
        fullmsg           = get_validation_msgs(False, msg)
        row               = table.add_row()
        row.cells[0].text = fullmsg

# ── Use for testing validation/error handling functions───────────────────────────────
if __name__ == "__main__":
    print(f"Using CSV file: {CSV_FILE}")

    get_csv_checks(CSV_FILE)
    get_dtype_checks(CSV_FILE)
    get_timestamp_checks(CSV_FILE)
    reportdoc.save(REPORT_FILE)
