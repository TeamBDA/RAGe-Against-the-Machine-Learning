import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pytest
import pandas as pd
from io import StringIO
from docx import Document
import src.validate_transcriptions as ivc

# Helper: create a dummy Word table for logging
def make_table():
    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    return table

# ---------------------------------------------------------
# 1. Empty CSV → get_csv_checks should raise EmptyDataError
# ---------------------------------------------------------
def test_empty_csv_raises_error():
    table = make_table()
    with pytest.raises(pd.errors.EmptyDataError):
        df = pd.read_csv(StringIO(""), **ivc.PARAMS["csv_read"])
        ivc.get_csv_checks(df, table)

# ---------------------------------------------------------
# 2. Timestamp column exists
# ---------------------------------------------------------
def test_timestamp_column_exists():
    table = make_table()
    df = pd.DataFrame({
        "num_words": [10],
        "speech_rate_wps": [2],
        "speaker_turn_id": [1],
        "total_speaking_time_seconds": [5],
        "question_flag": ["true"]
    })

    ivc.get_timestamp_checks(df, table, "timestamp")
    assert "timestamp" in table.rows[-1].cells[0].text.lower()

# ---------------------------------------------------------
# 3. Empty cells → get_csv_checks logs errors
# ---------------------------------------------------------
def test_empty_cells_logged():
    table = make_table()
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 12:00:00"],
        "num_words": [None],
        "speech_rate_wps": [2],
        "speaker_turn_id": [1],
        "total_speaking_time_seconds": [5],
        "question_flag": ["true"]
    })

    ivc.get_csv_checks(df, table)
    assert any("empty cell" in row.cells[0].text.lower() for row in table.rows)

# ---------------------------------------------------------
# 4. Numeric columns validation
# ---------------------------------------------------------
def test_numeric_columns_are_numeric():
    table = make_table()
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 12:00:00"],
        "num_words": ["abc"],  # invalid
        "speech_rate_wps": [2],
        "speaker_turn_id": [1],
        "total_speaking_time_seconds": [5],
        "question_flag": ["true"]
    })

    result = ivc.get_dtype_checks(
        df,
        table,
        ivc.PARAMS["dtype_checks"]["cols_int"],
        ivc.PARAMS["dtype_checks"]["col_bool"]
    )

    assert result is None
    assert any("missing expected numeric column" in row.cells[0].text.lower()
               for row in table.rows)

# ---------------------------------------------------------
# 5. Timestamp format validation
# ---------------------------------------------------------
def test_timestamp_format_invalid():
    table = make_table()
    df = pd.DataFrame({
        "timestamp": ["not-a-date"],
        "num_words": [10],
        "speech_rate_wps": [2],
        "speaker_turn_id": [1],
        "total_speaking_time_seconds": [5],
        "question_flag": ["true"]
    })

    ivc.get_timestamp_checks(df, table, "timestamp")
    assert "timestamp validation failed" in table.rows[-1].cells[0].text.lower()

# ---------------------------------------------------------
# 6. Boolean column validation
# ---------------------------------------------------------
def test_boolean_column_invalid():
    table = make_table()
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 12:00:00"],
        "num_words": [10],
        "speech_rate_wps": [2],
        "speaker_turn_id": [1],
        "total_speaking_time_seconds": [5],
        "question_flag": ["maybe"]  # invalid
    })

    result = ivc.get_dtype_checks(
        df,
        table,
        ivc.PARAMS["dtype_checks"]["cols_int"],
        ivc.PARAMS["dtype_checks"]["col_bool"]
    )

    assert result is None
    assert any("invalid boolean" in row.cells[0].text.lower()
               for row in table.rows)
    
    # ---------------------------------------------------------
# 7. Row count valid (>=25)
# ---------------------------------------------------------
def test_row_count_valid():
    table = make_table()
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 12:00:00"] * 25,
        "num_words": [10] * 25,
        "speech_rate_wps": [2] * 25,
        "speaker_turn_id": [1] * 25,
        "total_speaking_time_seconds": [5] * 25,
        "question_flag": ["true"] * 25
    })

    result = ivc.get_csv_checks(df, table)
    assert result is None
    assert "row count (25) is valid" in table.rows[-1].cells[0].text.lower()

# ---------------------------------------------------------
# 8. Row count too small (<25)
# ---------------------------------------------------------
def test_row_count_too_small():
    table = make_table()
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 12:00:00"] * 10,
        "num_words": [10] * 10,
        "speech_rate_wps": [2] * 10,
        "speaker_turn_id": [1] * 10,
        "total_speaking_time_seconds": [5] * 10,
        "question_flag": ["true"] * 10
    })

    ivc.get_csv_checks(df, table)
    assert "below the minimum" in table.rows[-1].cells[0].text.lower()