import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"


def ask_gemini(prompt):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text


if __name__ == "__main__":
    print("Testing Gemini...")

    answer = ask_gemini(
        "Give me 3 interesting tourist places in Tokyo, Japan."
    )

    print("\nGemini response:\n")
    print(answer)