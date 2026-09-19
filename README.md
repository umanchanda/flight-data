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
uv sync
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
uv run src/load_flights_to_neon.py
```

Re-running with a newer export will upsert — new flights are inserted, existing ones are updated.

### 5. Run the API locally
```bash
uv run uvicorn src.api.main:app --reload
```

### 6. Run the React app
```bash
cd frontend
npm install
npm run dev
```

The React app reads flight data through the API. For a local API, no extra
configuration is needed. For a deployed API, create `frontend/.env` with:
```
FLIGHT_API_URL=https://your-api.example.com
```

Create a production bundle with `npm run build` and serve `frontend/dist` with
your preferred static hosting provider.

### 7. Deploy the React frontend to Heroku

The API is already deployed at `https://flight-data-26kb.onrender.com`. Deploy
the React frontend as a separate Heroku app. The Node buildpack builds
`frontend/dist`, and the Heroku dyno serves those static files.

```bash
heroku login
heroku create your-flight-diary
heroku config:set FLIGHT_API_URL="https://flight-data-26kb.onrender.com"
git subtree push --prefix frontend heroku main
heroku open
```

`FLIGHT_API_URL` must be configured before the build because Vite embeds
it into the frontend bundle. The Render API already allows cross-origin `GET`
requests from the Heroku app. The frontend's [Procfile](frontend/Procfile)
starts the static server, while the root [Procfile](Procfile) remains the
FastAPI command used by Render.

Interactive docs available at `http://localhost:8000/docs`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/flights` | All flights — filterable by airline, aircraft, route, class, reason, ticket type, date range |
| `GET` | `/flights/{id}` | Single flight by ID |
| `GET` | `/stats` | Total flights, hours, airlines, airports |
| `GET` | `/aircraft` | All aircraft types with flight counts and hours |
| `GET` | `/airports` | All airports with departure/arrival counts |

The API is deployed at **https://flight-data-26kb.onrender.com**. Interactive docs at [https://flight-data-26kb.onrender.com/docs](https://flight-data-26kb.onrender.com/docs).

Example: `GET https://flight-data-26kb.onrender.com/flights?airline=United&flight_class=business&date_from=2024-01-01`

## Deploying the API

### Render (free tier)
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Set the following:
   - **Runtime:** Python
   - **Build command:** `pip install uv && uv sync --frozen`
   - **Start command:** `uv run uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment**, add `NEON_DATABASE_URL` with your connection string

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
├── Procfile                # API start command for Render
├── pyproject.toml          # Project metadata & dependencies (uv)
├── uv.lock                 # Locked dependency versions (uv)
├── csv/                    # Flight diary exports (gitignored)
└── .env                    # Database credentials (gitignored)
```
