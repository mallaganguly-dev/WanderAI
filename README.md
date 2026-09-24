# Travel Planner Agent

Three-agent CrewAI system that creates personalized travel itineraries with destination research, day-by-day plans, and budget breakdown.

**Framework**: CrewAI  
**LLM**: GPT-4o-mini  

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
python agent.py --destination "Tokyo, Japan" --days 7 --budget 3000
python agent.py --destination "Paris, France" --days 5 --budget 5000 --interests "art, wine, architecture"

## Web UI (Flask)

A lightweight Flask UI is included at `web.py`. It uses an Ollama model (`gpt-oss:120b-cloud`) to generate itineraries.

Prerequisites:
- Run Ollama and load the `gpt-oss:120b-cloud` model locally. See https://ollama.com/docs

Run locally:

```bash
pip install -r requirements.txt
export OLLAMA_URL="http://localhost:11434/api/generate"  # optional
python web.py
```

Then open http://localhost:5000 in your browser.
```
