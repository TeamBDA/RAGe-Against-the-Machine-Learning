from google import genai
import pandas as pd
import time

client = genai.Client(api_key="AIzaSyDfTK4_bX6y_Q8bMG2qB3_ARYJbkHUWOzs")

df = pd.read_csv("data/transcript/mock_transcripts.csv", encoding="utf-8-sig")
print(df.columns.tolist())

def correct_text(raw_text):
    prompt = f"Correct the spelling, grammar and punctuation of this text. Do not change the meaning. Return only the corrected sentence, nothing else: {raw_text}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()

df["text"] = df["raw_text_vosk"].apply(lambda x: (time.sleep(1), correct_text(x))[1])

df.to_csv("data/transcript/corrected_transcripts.csv", index=False)
print("Done! Saved to data/transcript/corrected_transcripts.csv")