
import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found")
    exit()

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"

models = [
    "gemini-3-flash-preview",
 
    "gemma-4-26b-a4b-it",
]

prompt = """
Create a short travel itinerary for Tokyo, Japan.

Trip duration: 5 days
Budget: $2000 USD
Interests: food, culture, anime
Travel style: Balanced

Give:
1. Three places to visit
2. Two restaurant suggestions
3. One hotel suggestion
4. A simple day-by-day itinerary
5. Approximate costs

Keep the total estimated cost within the $2000 budget.
Use plain text only. Do not use JSON or code.
"""

print("=" * 70)
print("        WANDERAI - REAL ITINERARY MODEL TEST")
print("=" * 70)

for number, model in enumerate(models, 1):

    print()
    print(f"[{number}/{len(models)}] TESTING: {model}")
    print("-" * 70)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        if response and response.text:
            print("SUCCESS")
            print()
            print(response.text[:3000])

        else:
            print("EMPTY RESPONSE")

    except Exception as e:
        print("FAILED")
        print("ERROR:", str(e)[:500])

    print()
    print("=" * 70)

    time.sleep(3)

print()
print("TEST FINISHED")
