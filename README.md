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

### 5. Run the Streamlit app
```bash
streamlit run app.py
```

### 6. Run the API locally
```bash
uvicorn api:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/flights` | All flights — filterable by airline, aircraft, route, class, reason, ticket type, date range |
| `GET` | `/flights/{id}` | Single flight by ID |
| `GET` | `/stats` | Total flights, hours, airlines, airports |
| `GET` | `/aircraft` | All aircraft types with flight counts and hours |
| `GET` | `/airports` | All airports with departure/arrival counts |

Example: `GET /flights?airline=United&flight_class=business&date_from=2024-01-01`

## Deploying the API

### Render (free tier)
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Set the following:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Under **Environment**, add `NEON_DATABASE_URL` with your connection string

### Railway
1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Under **Variables**, add `NEON_DATABASE_URL` with your connection string
3. Railway auto-detects the `Procfile` and starts the server

## Project structure
```
fr24/
├── app.py                  # Streamlit flights page (main entry point)
├── api.py                  # FastAPI REST API
├── load_flights_to_neon.py # CSV → Neon PostgreSQL loader
├── Procfile                # API start command for Render / Railway
├── requirements.txt
├── pages/
│   ├── 2_Aircraft.py       # Aircraft info & stats
│   └── 3_Airports.py       # Airport map & stats
├── csv/                    # Flight diary exports (gitignored)
└── .env                    # Database credentials (gitignored)
```
