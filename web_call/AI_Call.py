from google import genai
import sys
import os
from dotenv import load_dotenv

# Load API key from environment variable
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Configure the GenAI client with the API key
client = genai.Client(api_key=api_key)

class AI_call:
    def __init__(self, prompt):
        # Generate content
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt)
        # Print the response
        print(response.text, flush=True)

if __name__ == "__main__":
    prompt = sys.argv[1]
    AI_call(prompt)
