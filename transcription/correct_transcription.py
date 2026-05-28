# Import the Google Gemini AI client for transcript correction
from google import genai
# Import pandas for reading and writing CSV files
import pandas as pd
# Import time to add delays between API calls to avoid hitting rate limits
import time

# Create a variable for key, change the value to  actual key before running
my_api_key = "INSERT-KEY-HERE"

# Initialize the client
client = genai.Client(api_key=my_api_key)

# Load the mock CSV file containing raw Vosk transcripts
# utf-8-sig encoding handles hidden characters that Windows sometimes adds to files
df = pd.read_csv("data/transcript/mock_transcripts.csv", encoding="utf-8-sig")

# Define a function to send a raw transcript to Gemini and return the corrected version
def correct_text(raw_text):
    prompt = f"Correct the spelling, grammar, and punctuation of this text. Do not change the meaning. Return only the corrected sentence, nothing else: {raw_text}"
    
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Default sleep to stay well under the 15 RPM limit
            time.sleep(12.5) 
            
            return response.text.strip()
            
        except Exception as e:
            # If we hit the rate limit, wait 15 seconds and let the while loop try again
            if "429" in str(e):
                retries += 1
                print(f"Rate limit hit. Retry {retries} of {max_retries}. Waiting 15 seconds...")
                time.sleep(15)
            else:
                # If it is a different kind of error, raise it so you know what went wrong
                raise e
                
    # If it fails 3 times, raise an error to stop the script
    raise Exception("Max retries reached. You have likely exhausted your daily API quota.")

# Apply the function to the column to create the new "text" column
df["text"] = df["raw_text_vosk"].apply(correct_text)

# Print the column names to prove the 'text' column exists
print("Columns in memory right now:", df.columns.tolist())

# Print the first two rows to see the actual data
print(df.head(2))

# Save the updated dataframe with the corrected "text" column to a new CSV file
df.to_csv("data/transcript/corrected_transcripts.csv", index=False)
print("Done! Saved to data/transcript/corrected_transcripts.csv")