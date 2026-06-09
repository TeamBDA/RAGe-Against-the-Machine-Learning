# Import the Google Gemini AI client for transcript correction
from google import genai
<<<<<<< HEAD
# Explicitly import the error classes to prevent NameErrors during API hiccups
from google.genai.errors import APIError, ServerError, ClientError
=======
>>>>>>> d2d0e4debe6484e9de9655ce17f5a1eff9eac0bc
# Import pandas for reading and writing CSV files
import pandas as pd
# Import time to add delays between API calls to avoid hitting rate limits
import time

<<<<<<< HEAD
# Create a variable for key, change the value to  actual key before running
my_api_key = "YOUR API KEY HERE" #change this to actual API key before running

# Initialize the client
client = genai.Client(api_key=my_api_key)

# Load the mock CSV file containing raw Vosk transcripts
# utf-8-sig encoding handles hidden characters that Windows sometimes adds to files
df = pd.read_csv("INSERT FILE PATH HERE", encoding="utf-8-sig") #change this to file path

# Define a function to send a raw transcript to Gemini and return the corrected version
def correct_text(raw_text):
    # Handle empty or non-string rows gracefully without breaking the loop
    if not isinstance(raw_text, str) or not raw_text.strip():
        return raw_text

    prompt = f"Correct the spelling, grammar, and punctuation of this text. Do not change the meaning. Return only the corrected sentence, nothing else: {raw_text}"
    
    max_retries = 5
    retries = 0
    base_delay = 5  # Start with a 5-second wait on a failure

    while retries < max_retries:
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", #can change to other models for faster responses 
                contents=prompt
            )
            
            # Default sleep to stay safely under the 15 RPM limit for free accounts
            time.sleep(12.5) 
            return response.text.strip()
            
        except (ServerError, ClientError, APIError) as e:
            # Print the exact error text from Google, then stop the script
            print(f"\n[API ERROR] The script stopped because Google returned an error:")
            print(f"Details: {str(e)}\n")
            raise e
        except Exception as e:
            # Catch any other unexpected system or connection errors
            raise e
                
    # If it fails after all 5 attempts, raise an error explaining the server situation
    raise Exception(f"Failed after {max_retries} retries for text: '{raw_text[:30]}...'. Google servers are heavily overloaded right now. Try running the script later.")

# Read from the "transcript" column and save to a new "corrected_transcript" column
df["corrected_transcript"] = df["transcript"].apply(correct_text)

# Print the column names to prove the 'corrected_transcript' column exists
print("Columns in memory right now:", df.columns.tolist())

# Print the first two rows to see the actual data
print(df.head(2))

# Save the updated dataframe with the corrected "corrected_transcript" column to a new CSV file
df.to_csv("data/transcript/corrected_transcripts.csv", index=False)
print("Done! The corrected transcripts have been saved to 'corrected_transcripts.csv'.")
=======
# Initialise the Gemini client - replace YOUR_API_KEY_HERE with your key from https://aistudio.google.com/apikey
client = genai.Client(api_key="YOUR_API_KEY_HERE")

# Load the mock CSV file containing raw Vosk transcripts
# utf-8-sig encoding handles hidden characters that Windows sometimes adds to files
df = pd.read_csv("data/transcript/mock_transcripts.csv", encoding="utf-8-sig")

# Define a function to send a raw transcript to Gemini and return the corrected version
def correct_text(raw_text):
    # Build a prompt instructing Gemini to fix spelling, grammar and punctuation without changing the meaning
    prompt = f"Correct the spelling, grammar and punctuation of this text. Do not change the meaning. Return only the corrected sentence, nothing else: {raw_text}"
    # Send the prompt to Gemini and get the response
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    # Return the corrected text with any extra whitespace removed
    return response.text.strip()

# Apply the correct_text function to every row in the raw_text_vosk column
# time.sleep(1) adds a 1 second pause between each API call to avoid rate limiting
# The corrected result is saved in a new column called "text"
df["text"] = df["raw_text_vosk"].apply(lambda x: (time.sleep(1), correct_text(x))[1])

# Save the updated dataframe with the corrected "text" column to a new CSV file
df.to_csv("data/transcript/corrected_transcripts.csv", index=False)
print("Done! Saved to data/transcript/corrected_transcripts.csv")
>>>>>>> d2d0e4debe6484e9de9655ce17f5a1eff9eac0bc
