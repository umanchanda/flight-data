# fr24 Flight Diary

A Streamlit dashboard for visualizing personal flight history exported from [Flightradar24](https://www.flightradar24.com/).

## Features

### Flights page
- Summary metrics: total flights, hours flown, airlines, and airports visited
- Filterable flight table by airline, route, class, aircraft type, seat type, flight reason, ticket type, and date range
- Charts: flights by airline, flights per year, top routes, hours by airline

### Aircraft page
- Specs for every aircraft type you've flown (range, capacity, engines, wingspan, etc.)
- Personal stats per type: flights, hours, airlines, and routes

### Airports page
- World map of every airport you've visited
- Per-airport detail: name, city, country, IATA/ICAO codes, elevation, timezone
- Departures, arrivals, and airlines at each airport

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/fr24.git
cd fr24
```

### 2. Install dependencies
```bash
pip install streamlit pandas psycopg2-binary sqlalchemy python-dotenv airportsdata
```

### 3. Configure environment
Create a `.env` file in the project root:
```
NEON_DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

### 4. Load your flight data
Export your flight diary CSV from Flightradar24, place it in the `csv/` folder, update `CSV_PATH` in `load_flights_to_neon.py`, then run:
```bash
python3 load_flights_to_neon.py
```

Re-running with a newer export will upsert — new flights are inserted, existing ones are updated.

### 5. Run the app
```bash
streamlit run app.py
```

## Project structure
```
fr24/
├── app.py                  # Flights page (main entry point)
├── load_flights_to_neon.py # CSV → Neon PostgreSQL loader
├── pages/
│   ├── 2_Aircraft.py       # Aircraft info & stats
│   └── 3_Airports.py       # Airport map & stats
├── csv/                    # Flight diary exports (gitignored)
└── .env                    # Database credentials (gitignored)
```

## Database

Uses [Neon](https://neon.tech/) serverless PostgreSQL. The loader creates the `flight_diary` table automatically on first run and adds a unique constraint on `(date, from_airport, to_airport, dep_time)` to support upserts.
