# ── Info for error handling and validation check functions──────────────────────────────────────────────────────
#Use try/catch (Err Ex handling)
#Step: Get CSV and check rows/cols:
#Before analytics, your code should check that the final CSV is usable (the CSV has at least 25 rows).
#At minimum, check:
#No required values are missing.
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
import csv
from json.decoder import NaN

import pandas as pd
from pip._internal import self_outdated_check


def get_validation_msgs(success, failure):
    """
    """
def get_csv_checks(csv_file):
    """
    return: Set count of rows should be 25 or <
    """
    with (open(csv_file) as csvfile):
        """
        Skip presence of headers (i.e. text no numerical)
        Read csv and ensure there are no blank lines and the header is skipped
        then count rows of alphanumeric data
        """
        rowlength    = None
        emptiesFound = False
        try:
            """
            IMPORTANT: run row count last as we need to check for malformed row/cols first
            Check for nul cols
            """
            readcsv           = pd.read_csv(csvfile,
            header=0,
            skip_blank_lines=True,
            na_values=["", " "]
            )

            readcsv           = readcsv.apply(lambda    col:col.map(lambda x: x.strip() if isinstance(x, str) else x))
            """
            Check for empty column/cells
            """
            empty_cells       = pd.isna(readcsv)

            for row, col in zip(*empty_cells.to_numpy().nonzero()):
                emptiesFound = True
                print(f"column is empty at row: {row} and column: {col}")

            if not(emptiesFound):
                print(f"There are no empty columns or cells in the csv file")

                """
                Row count
                """
                rowlength = len(readcsv)
                print(f"There are {rowlength} rows in the csv file")

        except pd.errors.EmptyDataError:
            print(f"There are errors in the csv file")
    return rowlength

def get_timestamp_checks(): """
def get_speech_checks():
"""#

if __name__ == "__main__":
  get_csv_checks("../data/transcriptions - vosk_0.15.csv")
