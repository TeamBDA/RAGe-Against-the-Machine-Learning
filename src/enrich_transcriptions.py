import os
import pandas as pd

# project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data/results")

def load_data(file_path):
    """Load data from a CSV file."""
    return pd.read_csv(file_path)

def add_question_flag(df):
    """Add a boolean column indicating if the transcript ends
    with a question mark."""
    df['question_flag'] = df['corrected_transcript'].str.endswith('?')
    return df

def add_num_words(df):
    """Add a column for the number of words in the transcript."""
    df['num_words'] = df['corrected_transcript'].str.split().apply(len)
    return df

def add_text_size_chars(df):
    """Add a column for the number of characters in the transcript."""
    df['text_size_chars'] = df['corrected_transcript'].str.len()
    return df

# speech_rate_wps	num_words / time_taken_sec, rounded sensibly.
def add_speech_rate(df):
    """Add a column for speech rate in words per second."""
    df['speech_rate_wps'] = (
        df['num_words'] / df['total_speaking_time_seconds']
        ).round(2)
    return df

def add_speaker_turn_id(df):
    """Add a column for speaker turn ID, to track number of times
    each speaker speaks."""
    df['speaker_turn_id'] = df.groupby('speaker')['corrected_transcript'].cumcount() + 1
    return df

def save_enriched_data(df, output_file):
    """Save the enriched DataFrame to a new CSV file."""
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    # Example usage
    filename = 'corrected_transcripts.csv'
    file_path = os.path.join(
        TRANSCRIPTIONS_DIR, filename,
        )
    df = load_data(file_path)
    df = add_question_flag(df)
    df = add_num_words(df)
    df = add_text_size_chars(df)
    df = add_speech_rate(df)
    df = add_speaker_turn_id(df)
    
    # Save the enriched DataFrame to a new CSV file
    output_file = os.path.join(
        TRANSCRIPTIONS_DIR, 'enriched_transcripts.csv',
        )
    save_enriched_data(df, output_file)
    print(f"Enriched data saved to {output_file}.")