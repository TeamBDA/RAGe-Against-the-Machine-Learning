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

if __name__ == "__main__":

    # Prompt the user to input their Google Gemini API key securely at runtime
    my_api_key = input("Please enter your Google Gemini API key: ")

    # Initialize the client
    client = genai.Client(api_key=my_api_key)

    # Load the mock CSV file containing raw Vosk transcripts
    # utf-8-sig encoding handles hidden characters that Windows sometimes adds to files
    df = pd.read_csv(r"./data/results/transcriptions.csv", encoding="utf-8-sig")

    # Ensure the corrected_transcript column exists
    if "corrected_transcript" not in df.columns:
        df["corrected_transcript"] = None

    # Adding a 0.1s buffer is best practice to avoid edge-case rate limits
    PACING_DELAY = 4.1

    for index, row in tqdm(df.iterrows(), total=len(df), desc="Correcting Transcripts"):
        # Skip rows that have already been processed (useful if restarting a failed run)
        if df.at[index, "corrected_transcript"] is not None:
            continue
            
        raw_text = row["transcript"]
        
        # Call your corrected function (passing client explicitly)
        corrected_text_result = correct_text(client, raw_text)
        
        # Save it back to the DataFrame
        df.at[index, "corrected_transcript"] = corrected_text_result
        
        # Enforce the 15 RPM pacing limit
        time.sleep(PACING_DELAY)

    # Print the column names to prove the 'corrected_transcript' column exists
    print("\nColumns in memory right now:", df.columns.tolist())

    # Print the first two rows to see the actual data
    print(df.head(2))

    # Save the updated dataframe with the corrected "corrected_transcript" column to a new CSV file
    df.to_csv(r"./data/results/corrected_transcripts.csv", index=False)
    print("Done! The corrected transcripts have been saved to 'corrected_transcripts.csv'.")