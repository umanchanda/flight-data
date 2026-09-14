# Flight Data

A React + FastAPI app for visualizing personal flight history exported from [Flightradar24](https://www.flightradar24.com/).

## Architecture

- **Frontend:** React app in `/home/runner/work/flight-data/flight-data/frontend`
- **Backend:** FastAPI app in `/home/runner/work/flight-data/flight-data/api`
- **Database:** Neon PostgreSQL
- **Deployment:** Render static site for the frontend and a Render web service for the API

The backend is the only layer that talks to Neon. The frontend reads all flight, aircraft, airport, and registration data through the API.

## Features

### Flights
- Summary metrics for flights, hours, airlines, and airports visited
- Multi-filter dashboard for years, airlines, airports, class, aircraft, seat type, reason, ticket type, and date range
- Charts for flights by airline, flights per year, top routes, and hours by airline
- Repeat-aircraft view for registrations flown more than once

### Aircraft
- Stats for each aircraft type you have flown
- Static aircraft specifications and intro text
- Airline and route breakdowns per aircraft type

### Airports
- Interactive world map of visited airports
- Airport detail cards with metadata and visit stats
- Route and airline breakdowns for each airport

### Registrations
- Per-registration flight history
- External aircraft metadata via ADSBDB
- Aircraft photos via Planespotters when available

## Local development

### 1. Install backend dependencies
```bash
cd /home/runner/work/flight-data/flight-data
python -m pip install -r requirements.txt
```

### 2. Install frontend dependencies
```bash
cd /home/runner/work/flight-data/flight-data/frontend
npm install
```

### 3. Configure environment variables
Create `/home/runner/work/flight-data/flight-data/.env`:
```env
NEON_DATABASE_URL=postgresql://...
FRONTEND_ORIGIN=http://localhost:5173
```

Create `/home/runner/work/flight-data/flight-data/frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Load your flight data
Export your flight diary CSV from Flightradar24, place it in the `csv/` folder, update `CSV_PATH` in `/home/runner/work/flight-data/flight-data/load_flights_to_neon.py`, then run:
```bash
cd /home/runner/work/flight-data/flight-data
python load_flights_to_neon.py
```

### 5. Run the API
```bash
cd /home/runner/work/flight-data/flight-data
uvicorn api.main:app --reload
```

Interactive docs are available at `http://localhost:8000/docs`.

### 6. Run the frontend
```bash
cd /home/runner/work/flight-data/flight-data/frontend
npm run dev
```

The React app runs at `http://localhost:5173`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/dashboard` | Dashboard data including summary metrics, filters, charts, flights, and repeat aircraft |
| `GET` | `/stats` | Global flight summary metrics |
| `GET` | `/flights` | Filtered flight list |
| `GET` | `/flights/{id}` | Single flight by ID |
| `GET` | `/aircraft` | All aircraft types with counts and hours |
| `GET` | `/aircraft/{name}` | Aircraft detail, specs, and route/airline stats |
| `GET` | `/airports` | All visited airports with map coordinates and visit counts |
| `GET` | `/airports/{code}` | Airport detail, visit stats, and route/airline breakdowns |
| `GET` | `/registrations` | All flown registrations |
| `GET` | `/registrations/{reg}` | Registration metadata, photo, stats, and flight history |

## Deploying to Render

This repo includes `/home/runner/work/flight-data/flight-data/render.yaml` for a two-service Render deployment.

### Backend service
- **Type:** Web Service
- **Root directory:** repo root
- **Build command:** `pip install uv && uv sync --frozen`
- **Start command:** `uv run uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- **Environment variables:**
  - `NEON_DATABASE_URL`
  - `FRONTEND_ORIGIN=https://<your-frontend>.onrender.com`

### Frontend service
- **Type:** Static Site
- **Root directory:** `frontend`
- **Build command:** `npm ci && npm run build`
- **Publish directory:** `dist`
- **Environment variables:**
  - `VITE_API_BASE_URL=https://<your-api>.onrender.com`

After the frontend is deployed, update `FRONTEND_ORIGIN` on the API service to the final Render URL for the frontend.

## Project structure

```text
flight-data/
├── api/
│   ├── aircraft_specs.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   └── routes/
│       ├── aircraft.py
│       ├── airports.py
│       ├── dashboard.py
│       ├── flights.py
│       ├── registrations.py
│       └── stats.py
├── frontend/
│   ├── public/
│   │   └── _redirects
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── utils.js
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── load_flights_to_neon.py
├── Procfile
├── pyproject.toml
├── render.yaml
├── requirements.txt
└── uv.lock
```
