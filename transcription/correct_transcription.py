# Import the Google Gemini AI client for transcript correction
from google import genai
# Import pandas for reading and writing CSV files
import pandas as pd
# Import time to add delays between API calls to avoid hitting rate limits
import time

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