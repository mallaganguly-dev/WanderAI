"""
WanderAI - Gemini + CrewAI Travel Planner

Run:
    python agent.py

Example:
    python agent.py --destination "Tokyo, Japan" --days 7 --budget 3000 --interests "food, culture, anime"
"""

import argparse
import os

from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM


load_dotenv()

def create_llm():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    models = [
        "gemini/gemini-3.8-flash",
        "gemini/gemini-3.7-flash",
        "gemini/gemini-3.6-flash",
        "gemini/gemini-3.5-flash-lite",
    ]

    for model in models:
        try:
            print(f"🤖 Trying Gemini model: {model}")

            llm = LLM(
                model=model,
                api_key=api_key,
            )

            # Test the model before giving it to CrewAI
            response = llm.call(
                "Reply with exactly: GEMINI_OK"
            )

            if response:
                print(f"✅ Gemini model available: {model}")
                return llm

        except Exception as e:
            print(f"⚠️ {model} unavailable: {e}")
            continue

    raise RuntimeError(
        "❌ No Gemini model is currently available. "
        "Please try again later."
    )


def build_travel_crew(
    destination: str,
    days: int,
    budget: float,
    interests: str
) -> str:

    llm = create_llm()

    # --------------------------------------------------
    # AGENT 1: DESTINATION RESEARCHER
    # --------------------------------------------------

    researcher = Agent(
        role="Destination Researcher",

        goal=(
            f"Research {destination} and provide useful travel "
            f"information for a {days}-day trip."
        ),

        backstory=(
            "You are an experienced international travel researcher "
            "who specializes in destinations, attractions, food, "
            "transportation, culture, safety and local experiences."
        ),

        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # --------------------------------------------------
    # AGENT 2: ITINERARY PLANNER
    # --------------------------------------------------

    planner = Agent(
        role="Travel Itinerary Planner",

        goal=(
            f"Create a detailed and realistic {days}-day itinerary "
            f"for {destination} within a ${budget} budget."
        ),

        backstory=(
            "You are an expert travel planner who creates practical "
            "day-by-day travel itineraries based on budget, interests "
            "and available time."
        ),

        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # --------------------------------------------------
    # AGENT 3: BUDGET ANALYST
    # --------------------------------------------------

    budget_analyst = Agent(
        role="Travel Budget Analyst",

        goal=(
            f"Create a realistic budget breakdown for a {days}-day "
            f"trip to {destination} with a total budget of ${budget}."
        ),

        backstory=(
            "You are a professional travel finance advisor who "
            "specializes in estimating accommodation, food, "
            "transportation, activities and other travel expenses."
        ),

        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # --------------------------------------------------
    # TASK 1: RESEARCH
    # --------------------------------------------------

    research_task = Task(
        description=f"""
Research {destination} for a {days}-day trip.

Traveler interests:
{interests}

Provide information about:

1. Best places to visit
2. Famous attractions
3. Hidden gems
4. Best neighborhoods to stay
5. Local food
6. Transportation
7. Cultural customs
8. Safety tips
9. Recommended activities
10. Approximate costs

Create a useful destination research report.
""",

        agent=researcher,

        expected_output=(
            "A detailed destination research report containing "
            "attractions, food, transportation, culture, safety "
            "and practical travel information."
        ),
    )

    # --------------------------------------------------
    # TASK 2: ITINERARY
    # --------------------------------------------------

    planning_task = Task(
        description=f"""
Create a detailed {days}-day travel itinerary for:

Destination: {destination}
Budget: ${budget}
Interests: {interests}

Use the destination research provided by the researcher.

For every day include:

- Morning
- Afternoon
- Evening
- Breakfast suggestion
- Lunch suggestion
- Dinner suggestion
- Main attractions
- Activities
- Transportation
- Approximate daily cost

Make the itinerary realistic and avoid putting distant locations
back-to-back unnecessarily.

The itinerary should be enjoyable, practical and suitable for the
traveler's interests.
""",

        agent=planner,

        expected_output=(
            f"A complete {days}-day itinerary with morning, "
            "afternoon and evening activities, meals, transportation "
            "and estimated costs."
        ),

        context=[research_task],
    )

    # --------------------------------------------------
    # TASK 3: BUDGET
    # --------------------------------------------------

    budget_task = Task(
        description=f"""
Create a detailed travel budget for:

Destination: {destination}
Duration: {days} days
Total budget: ${budget}
Interests: {interests}

Calculate approximate costs for:

1. Flights
2. Accommodation
3. Food
4. Local transportation
5. Attractions
6. Activities
7. Shopping
8. Emergency/miscellaneous expenses

Provide:

- Estimated total cost
- Daily average
- Category-wise breakdown
- Money-saving suggestions
- Whether the budget is sufficient
- Alternative cheaper options if necessary

Use the itinerary and research provided by the other agents.
""",

        agent=budget_analyst,

        expected_output=(
            "A complete itemized travel budget with category-wise "
            "costs, daily average, total estimated cost and "
            "money-saving recommendations."
        ),

        context=[research_task, planning_task],
    )

    # --------------------------------------------------
    # CREW
    # --------------------------------------------------

    crew = Crew(
        agents=[
            researcher,
            planner,
            budget_analyst
        ],

        tasks=[
            research_task,
            planning_task,
            budget_task
        ],

        process=Process.sequential,

        verbose=False,
    )

    result = crew.kickoff()

    return str(result)


# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="WanderAI - Smart Travel Planner"
    )

    parser.add_argument(
        "--destination",
        default="Tokyo, Japan",
        help="Travel destination"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of travel days"
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=3000,
        help="Total travel budget in USD"
    )

    parser.add_argument(
        "--interests",
        default="food, culture, history",
        help="Traveler interests"
    )

    args = parser.parse_args()

    print()
    print(
        f"✈️ Planning {args.days}-day trip to "
        f"{args.destination} (Budget: ${args.budget})"
    )
    print()

    try:

        itinerary = build_travel_crew(
            destination=args.destination,
            days=args.days,
            budget=args.budget,
            interests=args.interests
        )

        print()
        print("=" * 70)
        print("🗺️  WANDERAI TRAVEL ITINERARY")
        print("=" * 70)
        print()

        print(itinerary)

        print()
        print("=" * 70)
        print("✅ TRIP PLANNING COMPLETED")
        print("=" * 70)

    except Exception as e:

        print()
        print("❌ ERROR")
        print("-" * 70)
        print(str(e))
        print("-" * 70)


if __name__ == "__main__":
    main()