-- WanderAI schema for Cloudflare D1.
-- This creates an empty production database. Do not import private trip/admin rows
-- into a public Git repository.

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination TEXT NOT NULL,
    days INTEGER,
    budget REAL,
    interests TEXT,
    travel_style TEXT,
    itinerary TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_access INTEGER DEFAULT 1,
    is_main_admin INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);

CREATE INDEX IF NOT EXISTS idx_trips_created_at
    ON trips(created_at);
