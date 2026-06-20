from google import genai
from google.genai.errors import APIError, ServerError, ClientError
import pandas as pd
import time
from tqdm import tqdm

# Function to send a raw transcript to Gemini and return the corrected version
def correct_text(client, raw_text):
    # Handle empty or non-string rows gracefully without breaking the loop
    if not isinstance(raw_text, str) or not raw_text.strip():
        return raw_text

    prompt = f"Correct the spelling, grammar, and punctuation of this text. Do not change the meaning. Return only the corrected sentence, nothing else: {raw_text}"

    max_retries = 5
    base_delay = 5

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite", 
                contents=prompt
            )
            return response.text.strip()
            
        except (ServerError, ClientError, APIError) as e:
            if attempt == max_retries - 1:
                print(f"\n[API ERROR] Max retries reached. The script stopped because Google returned a persistent error:")
                print(f"Details: {str(e)}\n")
                raise e
            
            # If we have retries left, calculate exponential backoff and wait
            delay = base_delay * (2 ** attempt)
            print(f"\n[API Error] Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)

        except Exception as e:
            # Catch any other unexpected system or connection errors
            print(f"\n[Unexpected Error] {e}")
            raise e
                
    # If it fails after all 5 attempts, raise an error explaining the server situation
    raise Exception(f"Failed after {max_retries} retries for text: '{raw_text[:30]}...'. Google servers are heavily overloaded right now. Try running the script later.")

def run(df: "pd.DataFrame", api_key: str) -> "pd.DataFrame":
    """
    Pipeline entry point. Accepts a DataFrame from transcribe_recordings,
    adds a 'corrected_transcript' column, and returns the updated DataFrame.
    """
    client = genai.Client(api_key=api_key)
    PACING_DELAY = 4.1

    if "corrected_transcript" not in df.columns:
        df["corrected_transcript"] = None

    for index, row in tqdm(df.iterrows(), total=len(df), desc="Correcting Transcripts"):
        if df.at[index, "corrected_transcript"] is not None:
            continue
        df.at[index, "corrected_transcript"] = correct_text(client, row["transcript"])
        time.sleep(PACING_DELAY)

    print("✅ Correction complete.")
    return df


if __name__ == "__main__":

    # Prompt the user to input their Google Gemini API key securely at runtime
    my_api_key = input("Please enter your Google Gemini API key: ")

    # Load the mock CSV file containing raw Vosk transcripts
    # utf-8-sig encoding handles hidden characters that Windows sometimes adds to files
    df = pd.read_csv(r"./data/results/transcriptions.csv", encoding="utf-8-sig")

    # Clean transcriptions
    df = run(df, my_api_key)

    # Save the updated dataframe with the corrected "corrected_transcript" column to a new CSV file
    df.to_csv(r"./data/results/corrected_transcripts.csv", index=False)
    print("Done! The corrected transcripts have been saved to 'corrected_transcripts.csv'.")