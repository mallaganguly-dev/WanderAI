from flask import Flask, render_template, request
from google import genai
from dotenv import load_dotenv

import os
import time
import re
import requests
import sqlite3

from urllib.parse import quote_plus


load_dotenv()

app = Flask(__name__)


# ==================================================
# GEMINI API
# ==================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    MODEL,
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]


# ==================================================
# GOOGLE MAPS SEARCH LINK
# ==================================================

def google_maps_link(place, destination):

    query = f"{place}, {destination}"

    encoded_query = quote_plus(query)

    return (
        "https://www.google.com/maps/search/?api=1&query="
        + encoded_query
    )


# ==================================================
# GOOGLE MAPS LINKS
# ==================================================

def add_google_maps_links(itinerary, destination):

    # Clean escaped characters
    itinerary = itinerary.replace("\\#", "#")
    itinerary = itinerary.replace("\\&", "&")

    # Force location markers onto separate lines
    itinerary = re.sub(
        r"\s+(PLACE:)",
        r"\n\1",
        itinerary,
        flags=re.IGNORECASE
    )

    itinerary = re.sub(
        r"\s+(RESTAURANT:)",
        r"\n\1",
        itinerary,
        flags=re.IGNORECASE
    )

    itinerary = re.sub(
        r"\s+(HOTEL:)",
        r"\n\1",
        itinerary,
        flags=re.IGNORECASE
    )

    lines = itinerary.splitlines()

    output = []

    for line in lines:

        stripped = line.strip()

        match = re.match(
            r"^(PLACE|RESTAURANT|HOTEL):\s*(.+)$",
            stripped,
            flags=re.IGNORECASE
        )

        # Normal line
        if not match:

            output.append(line)

            continue

        kind = match.group(1).upper()

        place = match.group(2).strip()

        # Remove Markdown bold
        place = re.sub(
            r"\*\*",
            "",
            place
        )

        # Remove brackets
        place = place.strip("[]()")

        # Ignore empty values
        if not place:

            output.append(line)

            continue

        # Ignore placeholders
        if place.lower() in [
            "none",
            "n/a",
            "not available",
            "unknown",
            "a suitable hotel",
            "a specific restaurant"
        ]:

            output.append(line)

            continue

        # Create Maps URL
        maps_url = google_maps_link(
            place,
            destination
        )

        # Keep original line
        output.append(line)

        # Create button
        if kind == "PLACE":

            button_text = (
                f"📍 Open {place} in Google Maps"
            )

        elif kind == "RESTAURANT":

            button_text = (
                f"🍜 Find {place} on Google Maps"
            )

        else:

            button_text = (
                f"🏨 Find {place} on Google Maps"
            )

        output.append(
            f'<a href="{maps_url}" '
            f'target="_blank" '
            f'rel="noopener noreferrer" '
            f'class="maps-link">'
            f'{button_text}'
            f'</a>'
        )

    return "\n".join(output)


# ==================================================
# WEATHER
# ==================================================

def get_weather(destination):

    try:

        # ------------------------------------------
        # STEP 1: GEOCODING
        # ------------------------------------------

        geocode_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
        )

        geocode_response = requests.get(
            geocode_url,
            params={
                "name": destination,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=10
        )

        geocode_response.raise_for_status()

        geocode_data = geocode_response.json()

        if not geocode_data.get("results"):

            return None

        location = geocode_data["results"][0]

        latitude = location["latitude"]

        longitude = location["longitude"]

        city_name = location.get(
            "name",
            destination
        )

        country = location.get(
            "country",
            ""
        )

        # ------------------------------------------
        # STEP 2: WEATHER FORECAST
        # ------------------------------------------

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
        )

        weather_response = requests.get(
            weather_url,
            params={
                "latitude": latitude,
                "longitude": longitude,

                "current": (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "weather_code,"
                    "wind_speed_10m"
                ),

                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min"
                ),

                "forecast_days": 7,

                "timezone": "auto"
            },
            timeout=10
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        current = weather_data.get(
            "current",
            {}
        )

        daily = weather_data.get(
            "daily",
            {}
        )

        # ------------------------------------------
        # WEATHER DESCRIPTIONS
        # ------------------------------------------

        weather_codes = {

            0: "Clear sky",

            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",

            45: "Fog",
            48: "Depositing rime fog",

            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",

            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",

            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",

            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",

            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with heavy hail"
        }

        # ------------------------------------------
        # WEATHER ICONS
        # ------------------------------------------

        weather_icons = {

            0: "☀️",

            1: "🌤️",
            2: "⛅",
            3: "☁️",

            45: "🌫️",
            48: "🌫️",

            51: "🌦️",
            53: "🌦️",
            55: "🌧️",

            61: "🌧️",
            63: "🌧️",
            65: "🌧️",

            71: "🌨️",
            73: "❄️",
            75: "❄️",

            80: "🌦️",
            81: "🌧️",
            82: "⛈️",

            95: "⛈️",
            96: "⛈️",
            99: "⛈️"
        }

        # ------------------------------------------
        # 7-DAY FORECAST
        # ------------------------------------------

        forecast = []

        dates = daily.get(
            "time",
            []
        )

        codes = daily.get(
            "weather_code",
            []
        )

        max_temps = daily.get(
            "temperature_2m_max",
            []
        )

        min_temps = daily.get(
            "temperature_2m_min",
            []
        )

        forecast_count = min(
            len(dates),
            len(codes),
            len(max_temps),
            len(min_temps),
            7
        )

        for i in range(forecast_count):

            code = codes[i]

            forecast.append({

                "date": dates[i],

                "icon": weather_icons.get(
                    code,
                    "🌤️"
                ),

                "description": weather_codes.get(
                    code,
                    "Unknown"
                ),

                "max": round(
                    max_temps[i]
                ),

                "min": round(
                    min_temps[i]
                )
            })

        # ------------------------------------------
        # CURRENT WEATHER
        # ------------------------------------------

        current_code = current.get(
            "weather_code",
            0
        )

        return {

            "city": city_name,

            "country": country,

            "temperature": round(
                current.get(
                    "temperature_2m",
                    0
                )
            ),

            "feels_like": round(
                current.get(
                    "apparent_temperature",
                    0
                )
            ),

            "wind_speed": round(
                current.get(
                    "wind_speed_10m",
                    0
                )
            ),

            "weather_code": current_code,

            "description": weather_codes.get(
                current_code,
                "Unknown"
            ),

            "icon": weather_icons.get(
                current_code,
                "🌤️"
            ),

            "forecast": forecast
        }

    except Exception as e:

        print(
            f"⚠️ Weather error: {e}"
        )

        return None


# ==================================================
# CURRENCY CONVERSION
# ==================================================

def get_currency_info(destination, budget):

    try:

        currency_map = {

            "India": (
                "INR",
                "₹",
                "Indian Rupee"
            ),

            "Japan": (
                "JPY",
                "¥",
                "Japanese Yen"
            ),

            "United States": (
                "USD",
                "$",
                "US Dollar"
            ),

            "USA": (
                "USD",
                "$",
                "US Dollar"
            ),

            "United Kingdom": (
                "GBP",
                "£",
                "British Pound"
            ),

            "UK": (
                "GBP",
                "£",
                "British Pound"
            ),

            "France": (
                "EUR",
                "€",
                "Euro"
            ),

            "Germany": (
                "EUR",
                "€",
                "Euro"
            ),

            "Italy": (
                "EUR",
                "€",
                "Euro"
            ),

            "Spain": (
                "EUR",
                "€",
                "Euro"
            ),

            "Switzerland": (
                "CHF",
                "CHF",
                "Swiss Franc"
            ),

            "Australia": (
                "AUD",
                "A$",
                "Australian Dollar"
            ),

            "Canada": (
                "CAD",
                "C$",
                "Canadian Dollar"
            ),

            "Singapore": (
                "SGD",
                "S$",
                "Singapore Dollar"
            ),

            "Thailand": (
                "THB",
                "฿",
                "Thai Baht"
            ),

            "UAE": (
                "AED",
                "د.إ",
                "UAE Dirham"
            ),

            "Dubai": (
                "AED",
                "د.إ",
                "UAE Dirham"
            ),

            "South Korea": (
                "KRW",
                "₩",
                "South Korean Won"
            ),

            "China": (
                "CNY",
                "¥",
                "Chinese Yuan"
            ),

            "Malaysia": (
                "MYR",
                "RM",
                "Malaysian Ringgit"
            ),

            "Indonesia": (
                "IDR",
                "Rp",
                "Indonesian Rupiah"
            ),

            "Vietnam": (
                "VND",
                "₫",
                "Vietnamese Dong"
            )
        }

        destination_lower = destination.lower()

        target_currency = None

        symbol = ""

        currency_name = ""

        # Find destination currency
        for country, currency_data in currency_map.items():

            if country.lower() in destination_lower:

                target_currency = currency_data[0]

                symbol = currency_data[1]

                currency_name = currency_data[2]

                break

        # Currency not found
        if not target_currency:

            return None

        # User budget is treated as USD
        base_currency = "USD"

        # USD destination
        if target_currency == base_currency:

            return {

                "base_currency": "USD",

                "target_currency": target_currency,

                "symbol": symbol,

                "currency_name": currency_name,

                "original_amount": round(
                    float(budget),
                    2
                ),

                "converted_amount": round(
                    float(budget),
                    2
                ),

                "rate": 1
            }

        # Frankfurter API
        url = (
            "https://api.frankfurter.dev/v2/rate/"
            f"{base_currency.lower()}/"
            f"{target_currency.lower()}"
        )

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        rate = float(
            data["rate"]
        )

        converted_amount = (
            float(budget) * rate
        )

        return {

            "base_currency": base_currency,

            "target_currency": target_currency,

            "symbol": symbol,

            "currency_name": currency_name,

            "original_amount": round(
                float(budget),
                2
            ),

            "converted_amount": round(
                converted_amount,
                2
            ),

            "rate": rate
        }

    except Exception as e:

        print(
            f"⚠️ Currency conversion error: {e}"
        )

        return None


# ==================================================
# GENERATE ITINERARY
# ==================================================

def generate_itinerary(
    destination,
    days,
    budget,
    interests,
    travel_style
):

    prompt = f"""
You are WanderAI, a professional AI travel planning assistant.

Create a realistic {days}-day travel itinerary for a real traveler.

TRIP INFORMATION
----------------

Destination:
{destination}

Number of Days:
{days}

Total Budget:
${budget}

Traveler Interests:
{interests}

Travel Style:
{travel_style}


TRAVEL STYLE GUIDELINES
-----------------------

If the travel style is Budget:
- Prioritize affordable accommodation.
- Prefer public transportation.
- Recommend free or low-cost attractions.
- Keep food costs reasonable.

If the travel style is Balanced:
- Balance comfort, sightseeing, food and cost.
- Use practical transportation.
- Recommend good-value accommodation and activities.

If the travel style is Luxury:
- Prioritize premium accommodation.
- Recommend high-quality restaurants.
- Include convenient transportation.
- Include premium experiences where appropriate.
- Never exceed the user's total budget.

If the travel style is Adventure:
- Prioritize outdoor activities.
- Include nature and adventure experiences.
- Include active exploration.
- Keep the schedule realistic.

If the travel style is Family:
- Recommend family-friendly attractions.
- Avoid overly difficult activities.
- Include comfortable transportation.
- Consider different age groups.

If the travel style is Romantic:
- Include scenic locations.
- Recommend romantic experiences.
- Include good dining options.
- Keep the schedule relaxed.


IMPORTANT TRAVEL PLANNING RULES
------------------------------

1. Create a practical itinerary for a real traveler.
2. Prioritize the traveler's interests.
3. Group nearby attractions together.
4. Avoid unnecessary long-distance travel.
5. Do not overcrowd the schedule.
6. Include realistic travel times.
7. Recommend appropriate local transportation.
8. Include approximate prices.
9. Mention local currency when useful.
10. Keep the total estimated cost within the user's budget.
11. Include accommodation estimates.
12. Include food estimates.
13. Include transportation estimates.
14. Include attraction/activity estimates.
15. Calculate the approximate total cost.
16. Calculate the remaining budget.
17. Recommend real tourist attractions and commonly known places.
18. Do not invent impossible attractions.
19. Do not output JSON.
20. Do not output programming code.
21. Do not output technical information.
22. Do not discuss how you generated the itinerary.


HOTEL AND RESTAURANT RULES
--------------------------

For each day:

- Recommend 1 suitable hotel/accommodation option.
- Recommend 1 specific restaurant or food location.
- Use real, recognizable places whenever possible.
- Match recommendations to the destination, budget,
  travel style, and interests.
- Do not invent addresses, phone numbers, prices,
  ratings, or URLs.

Use exactly this format:

Accommodation:
HOTEL: [specific real hotel name]
Description: [short reason why it suits the traveler]

Food:
RESTAURANT: [specific real restaurant name]
Description: [recommended food or reason to visit]


REQUIRED FORMAT
---------------

# Trip Overview

Destination:
Duration:
Budget:
Travel Style:
Interests:


# Day 1

Morning:
PLACE: [specific real attraction]
Description: [what to do]

Afternoon:
PLACE: [specific real attraction]
Description: [what to do]

Evening:
PLACE: [specific real attraction]
Description: [what to do]

Accommodation:
HOTEL: [specific real hotel name]
Description: [short reason why it suits the traveler]

Food:
RESTAURANT: [specific real restaurant name]
Description: [food recommendation]

Transportation:
[transportation information]

Estimated Cost:
[cost]


# Day 2

Morning:
PLACE: [specific real attraction]
Description: [what to do]

Afternoon:
PLACE: [specific real attraction]
Description: [what to do]

Evening:
PLACE: [specific real attraction]
Description: [what to do]

Accommodation:
HOTEL: [specific real hotel name]
Description: [short reason why it suits the traveler]

Food:
RESTAURANT: [specific real restaurant name]
Description: [food recommendation]

Transportation:
[transportation information]

Estimated Cost:
[cost]


Continue this format for every day.


# Budget Breakdown

Accommodation:
Food:
Transportation:
Activities:
Other:
Total Estimated Cost:
Remaining Budget:


# Food Recommendations

RESTAURANT: [specific real restaurant or food location]
Description: [recommendation]


# Transportation

Explain the best ways to move around the destination.


# Practical Travel Tips

Provide useful tips about safety, local transport, timing, money,
weather, etiquette, and important travel considerations.


IMPORTANT OUTPUT RULES
----------------------

- Do NOT create Markdown links.
- Do NOT create Google Maps URLs.
- Do NOT write links such as [Place Name](URL).
- Do NOT include https://www.google.com/maps in your response.
- Only provide the PLACE name.
- Only provide the RESTAURANT name.
- Only provide the HOTEL name.
- Keep every PLACE entry on its own separate line.
- Keep every RESTAURANT entry on its own separate line.
- Keep every HOTEL entry on its own separate line.
- Keep all headings on separate lines.
- The WanderAI website will automatically create Google Maps buttons.
"""


    # ----------------------------------------------
    # GEMINI FALLBACK SYSTEM
    # ----------------------------------------------

    for model in MODELS:

        print(
            f"\n🤖 Trying model: {model}"
        )

        for attempt in range(2):

            try:

                print(
                    f"Attempt {attempt + 1}/2"
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response.text:

                    print(
                        f"✅ Success with {model}"
                    )

                    return response.text

                print(
                    f"⚠️ {model} returned an empty response."
                )

            except Exception as e:

                error = str(e)

                print(
                    f"❌ {model} error: {error}"
                )

                # Retry temporary Gemini errors
                if (
                    "503" in error
                    or "UNAVAILABLE" in error
                    or "high demand" in error.lower()
                ):

                    if attempt == 0:

                        print(
                            "⏳ Waiting 3 seconds before retry..."
                        )

                        time.sleep(3)

                    continue

                # Skip unavailable model
                if (
                    "404" in error
                    or "NOT_FOUND" in error
                ):

                    print(
                        f"⚠️ Skipping unavailable model: {model}"
                    )

                    break

                break


    return """
# AI Service Temporarily Busy

WanderAI could not connect to an available Gemini model right now.

Your website and API configuration are working correctly.

Please wait a short time and try Plan My Trip again.
"""


# ==================================================
# FORMAT ITINERARY
# ==================================================

def format_itinerary(itinerary):

    # Fix escaped characters
    itinerary = itinerary.replace(
        "\\#",
        "#"
    )

    itinerary = itinerary.replace(
        "\\&",
        "&"
    )

    # Convert Markdown links to HTML
    markdown_link_pattern = (
        r'\[([^\]]+)\]\((https?://[^)]+)\)'
    )

    def convert_markdown_link(match):

        text = match.group(1).replace(
            "**",
            ""
        )

        url = match.group(2).replace(
            "\\&",
            "&"
        )

        return (
            f'<a href="{url}" '
            f'target="_blank" '
            f'rel="noopener noreferrer" '
            f'class="maps-link">'
            f'{text}'
            f'</a>'
        )

    itinerary = re.sub(
        markdown_link_pattern,
        convert_markdown_link,
        itinerary
    )

    # Major headings
    major_headings = [

        "Trip Overview",

        "Budget Breakdown",

        "Food Recommendations",

        "Transportation",

        "Practical Travel Tips"
    ]

    for heading in major_headings:

        itinerary = re.sub(
            rf'\s+(#\s*{re.escape(heading)})',
            r'\n\1',
            itinerary,
            flags=re.IGNORECASE
        )

    # Day headings
    itinerary = re.sub(
        r'\s+(#\s*Day\s+\d+)',
        r'\n\1',
        itinerary,
        flags=re.IGNORECASE
    )

    # Common sections
    sections = [

        "Morning:",

        "Afternoon:",

        "Evening:",

        "Food:",

        "Transportation:",

        "Estimated Cost:",

        "Description:",

        "Accommodation:",

        "HOTEL:",

        "Activities:",

        "Other:",

        "Total Estimated Cost:",

        "Remaining Budget:",

        "PLACE:",

        "RESTAURANT:"
    ]

    for section in sections:

        itinerary = re.sub(
            rf'\s+({re.escape(section)})',
            r'\n\1',
            itinerary,
            flags=re.IGNORECASE
        )

    lines = itinerary.splitlines()

    html = []

    day_open = False

    overview_open = False

    for line in lines:

        line = line.strip()

        if not line:

            continue

        line = line.replace(
            "\\#",
            "#"
        )

        # ------------------------------------------
        # DAY HEADING
        # ------------------------------------------

        if re.match(
            r"^#\s*Day\s+\d+",
            line,
            re.IGNORECASE
        ):

            if day_open:

                html.append("</div>")

                day_open = False

            if overview_open:

                html.append("</div>")

                overview_open = False

            day_title = re.sub(
                r"^#\s*",
                "",
                line
            )

            html.append(
                '<div class="day-card">'
                f'<div class="day-title">{day_title}</div>'
            )

            day_open = True

        # ------------------------------------------
        # TRIP OVERVIEW
        # ------------------------------------------

        elif line.lower().startswith(
            "# trip overview"
        ):

            if day_open:

                html.append("</div>")

                day_open = False

            if overview_open:

                html.append("</div>")

            html.append(
                '<div class="overview-section">'
                '<div class="overview-title">'
                '🧭 Trip Overview'
                '</div>'
            )

            overview_open = True

        # ------------------------------------------
        # OTHER MAJOR HEADINGS
        # ------------------------------------------

        elif line.startswith("#"):

            if day_open:

                html.append("</div>")

                day_open = False

            if overview_open:

                html.append("</div>")

                overview_open = False

            title = line.lstrip("#").strip()

            html.append(
                '<div class="overview-section">'
                f'<div class="overview-title">'
                f'{title}'
                f'</div>'
            )

            overview_open = True

        # ------------------------------------------
        # GOOGLE MAPS LINK
        # ------------------------------------------

        elif (
            line.startswith("<a ")
            and "maps-link" in line
        ):

            html.append(line)

        # ------------------------------------------
        # PLACE / HOTEL / RESTAURANT
        # ------------------------------------------

        elif re.match(
            r"^(PLACE|HOTEL|RESTAURANT):",
            line,
            re.IGNORECASE
        ):

            marker_match = re.match(
                r"^(PLACE|HOTEL|RESTAURANT):\s*(.*)$",
                line,
                re.IGNORECASE
            )

            marker = marker_match.group(1).upper()

            value = marker_match.group(2).strip()

            if marker == "PLACE":

                icon = "📍"

            elif marker == "HOTEL":

                icon = "🏨"

            else:

                icon = "🍜"

            html.append(
                '<div class="location-name">'
                f'{icon} {value}'
                '</div>'
            )

        # ------------------------------------------
        # SECTION HEADINGS
        # ------------------------------------------

        elif (
            line.endswith(":")
            and len(line) < 40
        ):

            section = line[:-1].strip()

            icons = {

                "Morning": "🌅",

                "Afternoon": "☀️",

                "Evening": "🌆",

                "Food": "🍜",

                "Transportation": "🚆",

                "Estimated Cost": "💰",

                "Description": "📝",

                "Accommodation": "🏨",

                "Activities": "🎟️",

                "Other": "📦",

                "Total Estimated Cost": "💰",

                "Remaining Budget": "💵"
            }

            icon = icons.get(
                section,
                "📌"
            )

            html.append(
                '<div class="sub-heading">'
                f'{icon} {section}'
                '</div>'
            )

        # ------------------------------------------
        # BULLET POINTS
        # ------------------------------------------

        elif (
            line.startswith("* ")
            or line.startswith("- ")
        ):

            text = line[2:]

            text = text.replace(
                "**",
                ""
            )

            html.append(
                '<div class="bullet-item">'
                f'• {text}'
                '</div>'
            )

        # ------------------------------------------
        # NORMAL TEXT
        # ------------------------------------------

        else:

            text = line

            text = text.replace(
                "**",
                ""
            )

            text = text.replace(
                "*",
                ""
            )

            html.append(
                '<div class="normal-text">'
                f'{text}'
                '</div>'
            )

    # Close day
    if day_open:

        html.append("</div>")

    # Close overview
    if overview_open:

        html.append("</div>")

    return "\n".join(html)


# ==================================================
# TRIP HISTORY DATABASE
# ==================================================

DATABASE = "wanderai.db"


def init_database():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            destination TEXT NOT NULL,

            days INTEGER,

            budget REAL,

            interests TEXT,

            travel_style TEXT,

            itinerary TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


def save_trip(
    destination,
    days,
    budget,
    interests,
    travel_style,
    itinerary
):

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO trips
        (
            destination,
            days,
            budget,
            interests,
            travel_style,
            itinerary
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            destination,
            days,
            budget,
            interests,
            travel_style,
            itinerary
        )
    )

    connection.commit()

    connection.close()


def get_trip_history():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM trips
        ORDER BY created_at DESC
        """
    )

    trips = cursor.fetchall()

    connection.close()

    return trips


# Initialize database
init_database()


# ==================================================
# HOME PAGE
# ==================================================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    return render_template(
        "index.html"
    )


# ==================================================
# TRIP HISTORY PAGE
# ==================================================

@app.route(
    "/history"
)
def history():

    trips = get_trip_history()

    return render_template(
        "history.html",
        trips=trips
    )


# ==================================================
# VIEW SAVED TRIP
# ==================================================

@app.route(
    "/history/<int:trip_id>"
)
def view_trip(trip_id):

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM trips
        WHERE id = ?
        """,
        (trip_id,)
    )

    trip = cursor.fetchone()

    connection.close()

    if not trip:

        return "Trip not found", 404

    return render_template(
        "result.html",

        destination=trip["destination"],

        days=trip["days"],

        budget=trip["budget"],

        interests=trip["interests"],

        travel_style=trip["travel_style"],

        itinerary=trip["itinerary"],

        weather=None,

        currency=None
    )


# ==================================================
# PLAN TRIP
# ==================================================

@app.route(
    "/plan",
    methods=["POST"]
)
def plan():

    # ----------------------------------------------
    # DESTINATION
    # ----------------------------------------------

    destination = request.form.get(
        "destination",
        "Tokyo, Japan"
    ).strip()

    if not destination:

        destination = "Tokyo, Japan"


    # ----------------------------------------------
    # DAYS
    # ----------------------------------------------

    days_value = request.form.get(
        "days",
        "7"
    ).strip()

    try:

        days = int(days_value)

        if days < 1:

            days = 1

        if days > 30:

            days = 30

    except:

        days = 7


    # ----------------------------------------------
    # BUDGET
    # ----------------------------------------------

    budget_value = request.form.get(
        "budget",
        "3000"
    ).strip()

    try:

        budget = float(
            budget_value
        )

        if budget <= 0:

            budget = 3000.0

    except:

        budget = 3000.0


    # ----------------------------------------------
    # INTERESTS
    # ----------------------------------------------

    interests = request.form.get(
        "interests",
        "food, culture, history"
    ).strip()

    if not interests:

        interests = "food, culture, history"


    # ----------------------------------------------
    # TRAVEL STYLE
    # ----------------------------------------------

    travel_style = request.form.get(
        "travel_style",
        "Balanced"
    ).strip()

    if not travel_style:

        travel_style = "Balanced"


    # ----------------------------------------------
    # GENERATE ITINERARY
    # ----------------------------------------------

    itinerary = generate_itinerary(
        destination,
        days,
        budget,
        interests,
        travel_style
    )


    # ----------------------------------------------
    # REAL WEATHER
    # ----------------------------------------------

    weather = get_weather(
        destination
    )


    # ----------------------------------------------
    # CURRENCY CONVERSION
    # ----------------------------------------------

    currency = get_currency_info(
        destination,
        budget
    )


    # ----------------------------------------------
    # GOOGLE MAPS LINKS
    # ----------------------------------------------

    itinerary_with_maps = add_google_maps_links(
        itinerary,
        destination
    )


    # ----------------------------------------------
    # FORMAT ITINERARY
    # ----------------------------------------------

    itinerary_with_maps = format_itinerary(
        itinerary_with_maps
    )


    # ----------------------------------------------
    # SAVE TRIP
    # ----------------------------------------------

    save_trip(
        destination,
        days,
        budget,
        interests,
        travel_style,
        itinerary_with_maps
    )


    # ----------------------------------------------
    # SHOW RESULT
    # ----------------------------------------------

    return render_template(
        "result.html",

        destination=destination,

        days=days,

        budget=budget,

        interests=interests,

        travel_style=travel_style,

        itinerary=itinerary_with_maps,

        weather=weather,

        currency=currency
    )


# ==================================================
# RUN SERVER
# ==================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=True
    )