# fr24 Flight Diary

A React dashboard for visualizing personal flight history exported from [Flightradar24](https://www.flightradar24.com/), backed by FastAPI and Neon PostgreSQL.

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
pip install -r requirements.txt
```

### 3. Configure environment
Create a `.env` file in the project root:
```
NEON_DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
FLIGHT_API_URL=http://localhost:8000
```

### 4. Load your flight data
Export your flight diary CSV from Flightradar24, place it in the `csv/` folder, update `CSV_PATH` in `src/load_flights_to_neon.py`, then run:
```bash
python src/load_flights_to_neon.py
```

Re-running with a newer export will upsert — new flights are inserted, existing ones are updated.

### 5. Run the API locally
```bash
uvicorn src.api.main:app --reload
```

### 6. Run the React app
```bash
cd frontend
npm install
npm run dev
```

In local development the API and frontend run as separate processes, so the
frontend talks to the API at `http://localhost:8000` by default. No extra
configuration is needed unless you want to point it at a different API URL,
in which case set `FLIGHT_API_URL` in `frontend/.env` before building.

Interactive docs available at `http://localhost:8000/docs`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/flights` | All flights — filterable by airline, aircraft, route, class, reason, ticket type, date range |
| `GET` | `/flights/{id}` | Single flight by ID |
| `GET` | `/stats` | Total flights, hours, airlines, airports |
| `GET` | `/aircraft` | All aircraft types with flight counts and hours |
| `GET` | `/airports` | All airports with departure/arrival counts |

The app is deployed at **https://flight-data-26kb.onrender.com**. Interactive docs at [https://flight-data-26kb.onrender.com/docs](https://flight-data-26kb.onrender.com/docs).

Example: `GET https://flight-data-26kb.onrender.com/flights?airline=United&flight_class=business&date_from=2024-01-01`

## Deploying to Render

The API and React frontend deploy together as a single Render web service.
FastAPI serves the JSON API and also serves the built `frontend/dist` files,
so there's only one URL and no cross-origin configuration to manage.

The repo includes a [render.yaml](render.yaml) Blueprint with the required
settings, so you can deploy by connecting the repo and syncing the Blueprint:

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint → connect your repo
3. Render reads `render.yaml` and creates the web service automatically
4. Under **Environment**, set `NEON_DATABASE_URL` to your Neon connection string

To configure the service manually instead:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt && cd frontend && npm install && npm run build`
   - **Start command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

Render's Python runtime includes Node.js, so the same build step compiles the
React app before the API starts.

## Project structure
```
fr24/
├── src/
│   ├── api/
│   │   ├── main.py         # FastAPI app + middleware
│   │   ├── db.py           # DB connection, constants, helpers
│   │   ├── models.py       # Pydantic models
│   │   └── routes/
│   │       ├── flights.py  # GET /flights, GET /flights/{id}
│   │       ├── stats.py    # GET /stats
│   │       ├── aircraft.py # GET /aircraft
│   │       ├── airports.py # GET /airports
│   │       └── registrations.py # GET /registrations/{reg}
│   ├── registration_lookup.py  # External aircraft metadata
│   └── load_flights_to_neon.py # CSV → Neon PostgreSQL loader
├── frontend/
│   ├── src/App.jsx         # React dashboard and views
│   ├── src/api.js          # FastAPI client
│   └── src/styles.css      # Dashboard styling
├── render.yaml             # Single-service Render Blueprint
├── requirements.txt        # Python dependencies (pip)
├── csv/                    # Flight diary exports (gitignored)
└── .env                    # Database credentials (gitignored)
```
