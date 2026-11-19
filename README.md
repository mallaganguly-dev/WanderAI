# WanderAI — AI Travel Planner

WanderAI is a Flask web app that creates AI-generated travel itineraries using the Google Gemini API. It includes trip planning, weather information, currency conversion, Google Maps links, trip history, sign-up/login, and an admin panel.

## Technologies
- Python 3.12
- Flask (backend)
- HTML, CSS, JavaScript (frontend)
- SQLite (local/demo data storage)
- Google Gemini API (AI itinerary generation)
- Gunicorn (production web server)

## Run locally
1. Install Python 3.12.
2. Install web dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Gemini API key, secret key, and admin credentials.
4. Start: `python web.py`
5. Visit http://127.0.0.1:5000.

## Deploy free with Render
1. Sign in to Render and choose **New → Blueprint**.
2. Connect GitHub and select this repository.
3. Render reads `render.yaml` and creates the free web service.
4. Enter `GEMINI_API_KEY`, `MAIN_ADMIN_EMAIL`, and `MAIN_ADMIN_PASSWORD` when prompted. A `SECRET_KEY` is generated automatically.
5. Deploy. Render provides an HTTPS `onrender.com` URL.

**Free-plan notes:** the service may sleep when inactive. Free web services have ephemeral filesystems, so SQLite trip history and admin data may be lost after restarts/redeploys. This is suitable for a demo, not permanent storage.

## Standalone CrewAI agent (optional)
The web app does not need CrewAI installed. To run the CLI agent, install `pip install -r requirements-agent.txt`.

## Security
Do not commit `.env`, API keys, passwords, or SQLite databases. Use host environment variables for secrets.
