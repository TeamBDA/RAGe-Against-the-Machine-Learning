# ── Info for error handling and validation check functions──────────────────────────────────────────────────────
import os
import pandas as pd
import datetime
from docx import Document
from sklearn import pipeline
from sklearn.utils import validation

# ── Project Path Setup ──────────────────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR         = os.path.join(BASE_DIR, "documents")
REPORT_FILE        = os.path.join(REPORT_DIR, f"csvreport_{datetime.date.today()}.docx")
CSV_FILE           = os.path.join(TRANSCRIPTIONS_DIR, "transcriptions - vosk_0.15.csv")
# ── END Project Path Setup ───────────────────────────────────────────────────────────────

PARAMS = {
    "dtype_checks": {
        # Load CSV normally (no converters), specify cols to retrieve
        "cols_int": ['num_words', 'speech_rate_wps', 'speaker_turn_id'],
        "col_bool": 'question_flag',
        "header": 0
    },
    "csv_checks": {
        "header": 0,
        "skip_blank_lines": True,
        "na_values": ["", " ", "  "]
    },
    "timestamp_checks": {
        "header": 0
    }
}

def get_validation_msgs(success, message):
    """Prints a structured validation message."""
    status = "VALIDATION SUCCESS" if success else "VALIDATION FAILED"
    fullmsg= f"[{status}] {message}"
    print(fullmsg)
    return fullmsg

def log_error(table, msg):
    fullmsg = get_validation_msgs(False, msg)
    row = table.add_row()
    row.cells[0].text = fullmsg

def get_dtype_checks(df, table, cols_int, col_bool):
    """Data type validation logic."""
    # Arrs to collect all errors and a separate array to collect boolean data type errors to keep separated
    errors      = []
    validated_bools = []

    try:

        print(f"Data types for the columns are currently: {df.dtypes}")

        for col in cols_int:
            if col not in df.columns:
                msg = f"Missing expected numeric column: {col}"
                fullmsg = get_validation_msgs(False, msg)
                row = table.add_row()
                row.cells[0].text = fullmsg
                errors.append(fullmsg)
                continue

        # Integer/float numeric validation in few lines as possible by using pandas to conert to numeric and identify where its not a number or less than or equal to 0, then we can loop through the invalids and print out the row and column of the invalid entry for reporting
        converted = df[cols_int].apply(pd.to_numeric, errors='coerce')
        invalid_masked = converted.isna() | (converted <= 0)

        # stack the masked invalid entries to avoid looping thru entire df
        invalid_entries = invalid_masked.stack()
        invalid_entries = invalid_entries[invalid_entries]

        # Loop through the invalid numeric entries and print out the row and column of the invalid entry for reporting
        for idx, col, _ in invalid_entries.items():
           val = df.at[idx, col]
           if invalid_masked.at[idx, col]:
                    msg = f"Invalid numeric value '{val}' at column {col}"
                    fullmsg = get_validation_msgs(False, msg)
                    errors.append(fullmsg)
                    new_row = table.add_row()
                    new_row.cells[0].text = fullmsg

        # now deal with boolean True, false, 1,0, yes, no data type, again skip header row
        for idx, val in df[col_bool].items():

            sval = str(val).strip().lower()
            if sval in ("true", "1", "yes"):
                # Set boolean variable as True here as its is valid to track it
                bval = True
                validated_bools.append(True)
                print(f"[OK] Col {col_bool}: question_flag = {val}")
                # Replace string with real bool
                df.at[idx, col_bool] = bval
                continue
            elif sval in ("false", "0", "no"):
                # Set variable as False here for tracking
                bval = False
                validated_bools.append(False)
                print(f"[OK] Column {col_bool}: question_flag = {val}")
                # Replace string with real bool
                df.at[idx, col_bool] = bval
                continue
            else:
                # Any other outcome for the boolean data type should throw an exception, and append all exceptions found
                msg = f"Invalid boolean '{val}' at column {col_bool}"
                fullmsg = get_validation_msgs(False, msg)
                errors.append(fullmsg)
                row = table.add_row()
                row.cells[0].text = fullmsg
                validated_bools.append(None)
                continue

        # Replace string with real bool
        df.at[idx, col_bool] = val

        if errors:
            #log any errors
            log_error(table, "[VALIDATION FAILED] Data type validation failed.")

        else:
            # Return validation correct of all intended data met the data types requirements in file
            print("\n[VALIDATION SUCCESS] Data validation passed.")

    # exception to identify any exceptions that occur while running thru csv, and append to all errors
    except Exception as e:
        msg = f"Validation error: {e}"
        fullmsg           = get_validation_msgs(False, msg)
        errors.append(fullmsg)
        row               = table.add_row()
        row.cells[0].text = fullmsg

def get_csv_checks(df, table):
    """Validates CSV structure, empties, and row count."""
    # Intiailise row count to none initially
    rowlength = None

    try:
        # apply a lambda (once-off) function to apply mapping to strip extra spaces in csv columns that may exist
        df = df.apply(
            lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x)
        )

        # find indices of empty cells (NaN) using numpy
        empty_cells = pd.isna(df)
        row_indices, col_indices = empty_cells.to_numpy().nonzero()

        # If there are row indices to traverse
        if len(row_indices) > 0:
            for row, col in zip(row_indices, col_indices):
                msg = f"\n[VALIDATION FAILED] Data validation failed: Empty cell found at CSV line {row + 2}, Column index: {col}"
                fullmsg = get_validation_msgs(False, msg)
                new_row = table.add_row()
                new_row.cells[0].text = fullmsg

        else:
            print("There are no empty columns or cells in the CSV file.")

        # used to get row length input - capture no of rows in csv
        rowlength = len(df)
        print(f"There are {rowlength} data rows in the CSV file.")

        # find if there are more than the expected no of rows
        if rowlength >= 25:
            msg = f"Row count ({rowlength}) is valid (25 or more)."
            fullmsg = get_validation_msgs(True, msg)
            row = table.add_row()
            row.cells[0].text = fullmsg
        # capture where there are less than the no of expected rows
        else:
            msg = f"Row count ({rowlength}) is below the minimum required (25)."
            fullmsg = get_validation_msgs(False, msg)
            row = table.add_row()
            row.cells[0].text = fullmsg

    # catch exceptions where csv is empty
    except pd.errors.EmptyDataError:
        msg = "The CSV file is empty or has a malformed header."
        fullmsg = get_validation_msgs(False, msg)
        row  = table.add_row()
        row.cells[0].text = fullmsg
    # or file is not present
    except FileNotFoundError:
        msg =  f"File not found at: {CSV_FILE}"
        fullmsg = get_validation_msgs(False, msg)
        row = table.add_row()
        row.cells[0].text = fullmsg
    # or any generic exception
    except Exception as e:
        msg = f"An unexpected parsing error occurred: {str(e)}"
        fullmsg = get_validation_msgs(False, msg)
        row = table.add_row()
        row.cells[0].text = fullmsg
    # give us the row length
    return rowlength

def get_timestamp_checks(df, table):
    """Timestamp validation logic."""
    try:
        # intialise index to 0 before we check for timestamps
        idx = 0

        # check for occurence of the timestamp column in file
        if 'timestamp' not in df.columns:
            msg =  f"A timestamp column could not be found at row {idx}"
            fullmsg = get_validation_msgs(False, msg)
            row = table.add_row()
            row.cells[0].text = fullmsg
            return

        # Storing a copy of the timestamp so that it is output instead of null NaN val
        df['timestamp_raw'] = df['timestamp']

        # coerce timestamp to meet a readable date/time format
        df['timestamp'] = pd.to_datetime(
            df['timestamp'],
            format="mixed",
            errors="coerce"
        )

        # set variable for a timestamp that does not meet the expected output
        invalid_ts = df[df['timestamp'].isna()]

        # check for timestamp that is not empty first, so test the var above, then identify if the timestamp is in expected raw format
        if not invalid_ts.empty:
            for idx in invalid_ts.index:
                print(f"[INVALID] Row {idx + 2}: timestamp → '{df.loc[idx, 'timestamp_raw']}'")
            msg =  "Timestamp validation failed."
            fullmsg = get_validation_msgs(False, msg)
            row = table.add_row()
            row.cells[0].text = fullmsg
            return

        print("All timestamps are valid.")
        print(df['timestamp'])

        # format timestamp
        dttimeobj = df['timestamp'].iloc[0]
        formatted = dttimeobj.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Timestamp value {formatted}")

    #validate if the file is empty
    except pd.errors.EmptyDataError:
        msg = "The CSV file is empty."
        fullmsg = get_validation_msgs(False, msg)
        row = table.add_row()
        row.cells[0].text = fullmsg
    # capture any generic exceptions
    except Exception as e:
        msg = f"Timestamp validation error: {str(e)}"
        fullmsg = get_validation_msgs(False, msg)
        row = table.add_row()
        row.cells[0].text = fullmsg

# ── Use for testing validation/error handling functions───────────────────────────────
if __name__ == "__main__":

    print(f"Using CSV file: {CSV_FILE}")
    print(f"Validating CSV file: {CSV_FILE}")

    """Generate report from CSV file."""
    # Create a docx (Word) doc for reporting
    reportdoc = Document()
    # Add filename to report
    reportdoc.add_heading(f"Validation Checks Report on {datetime.date.today()} \n for file @: \n  {CSV_FILE}")

    # Create a table with 1 header and all rows and columns for the error report generated
    table = reportdoc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Error Description"

    """Run pipeline and generate report we will move this to the main pipeline script for the project later"""
    validation_pipeline = {
        "dtype_checks": get_dtype_checks,
        "csv_checks": get_csv_checks,
        "timestamp_checks": get_timestamp_checks
    }

    """Run read file exactly once within main by referencing different param set per function"""
    try:
      # Build unified read parameters
      READ_PARAMS = {
      "header": 0,
      "skip_blank_lines": True,
      "na_values": ["", " ", "  "],
      "usecols": PARAMS["dtype_checks"]["usecols"]  # all needed columns
      }

      df = pd.read_csv(CSV_FILE, **READ_PARAMS)

      '''Run all functions on df'''
      for name, func in validation_pipeline.items():
        func(df, table)
        """Adding table param"""
        validation_functions(df, table)

    except TypeError as e:
           print (f"[{PARAMS}] [FAILED]. Invalid parameter configuration error: {str(e)}")
    except Exception as e:
           print (f"[{PARAMS}] [VALIDATION FAILED]. Error: {str(e)}")

    # Save the final report
    reportdoc.save(REPORT_FILE)
