# Load environment variables from the .env file (keeps API keys out of the code)
from dotenv import load_dotenv
load_dotenv()

# Import the Google Gemini AI client for transcript correction
from google import genai

# Import pandas for reading and writing CSV files
import pandas as pd

# Import time to add delays between API calls (avoids hitting rate limits)
import time

# Initialise the Gemini client with our API key
client = genai.Client(api_key="GEMINI_API_KEY")

# Load the mock CSV file containing raw Vosk transcripts
# utf-8-sig encoding handles hidden characters that Windows sometimes adds to files
df = pd.read_csv("data/transcript/mock_transcripts.csv", encoding="utf-8-sig")

# Print column names to verify the CSV loaded correctly
print(df.columns.tolist())

def correct_text(raw_text):
    # Build a prompt that instructs Gemini to correct spelling, grammar and punctuation
    # without changing the meaning of the original text
    prompt = f"Correct the spelling, grammar and punctuation of this text. Do not change the meaning. Return only the corrected sentence, nothing else: {raw_text}"
    # Send the prompt to Gemini and get the corrected text back
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    # Return the corrected text, stripping any extra whitespace
    return response.text.strip()

# Apply the correct_text function to every row in the raw_text_vosk column
# time.sleep(1) adds a 1 second delay between each API call to avoid rate limiting
# The result is saved in a new column called "text"
df["text"] = df["raw_text_vosk"].apply(lambda x: (time.sleep(1), correct_text(x))[1])

# Save the updated dataframe with the new "text" column to a new CSV file
df.to_csv("data/transcript/corrected_transcripts.csv", index=False)
print("Done! Saved to data/transcript/corrected_transcripts.csv")