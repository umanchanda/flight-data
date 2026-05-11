import os
from datetime import date, time
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from registration_lookup import fetch_registration

load_dotenv()

app = FastAPI(
    title="Flight Diary API",
    description="Personal flight history from Flightradar24.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

SEAT_TYPE = {1: "Window", 2: "Middle", 3: "Aisle"}
FLIGHT_CLASS = {1: "Economy", 3: "Premium Economy", 2: "Business", 4: "First"}
FLIGHT_REASON = {1: "Personal", 2: "Business", 3: "Crew"}


def get_conn():
    return psycopg2.connect(
        os.environ["NEON_DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


# ── Models ─────────────────────────────────────────────────────────────────────

class Flight(BaseModel):
    id: int
    date: Optional[date]
    flight_number: Optional[str]
    from_airport: str
    to_airport: str
    dep_time: Optional[time]
    arr_time: Optional[time]
    duration_minutes: Optional[int]
    airline: str
    aircraft: Optional[str]
    registration: Optional[str]
    seat_number: Optional[str]
    seat_type: Optional[str]
    flight_class: Optional[str]
    flight_reason: Optional[str]
    note: Optional[str]


class Stats(BaseModel):
    total_flights: int
    total_hours: float
    unique_airlines: int
    unique_airports: int


class AircraftSummary(BaseModel):
    aircraft: str
    flights: int
    total_hours: float
    airlines: list[str]


class AirportSummary(BaseModel):
    code: str
    name: str
    city: str
    country: str
    departures: int
    arrivals: int
    total_visits: int


class RegistrationMeta(BaseModel):
    registration: str
    manufacturer: Optional[str]
    model: Optional[str]
    icao_type: Optional[str]
    operator: Optional[str]
    country: Optional[str]
    mode_s: Optional[str]
    photo_url: Optional[str]
    photo_thumbnail_url: Optional[str]


class RegistrationDetail(BaseModel):
    meta: Optional[RegistrationMeta]
    flights: list[Flight]


# ── Helpers ────────────────────────────────────────────────────────────────────

def row_to_flight(row: dict) -> Flight:
    duration = row["duration"]
    duration_minutes = int(duration.total_seconds() // 60) if duration else None
    return Flight(
        id=row["id"],
        date=row["date"],
        flight_number=row["flight_number"],
        from_airport=row["from_airport"],
        to_airport=row["to_airport"],
        dep_time=row["dep_time"],
        arr_time=row["arr_time"],
        duration_minutes=duration_minutes,
        airline=row["airline"],
        aircraft=row["aircraft"],
        registration=row["registration"],
        seat_number=row["seat_number"],
        seat_type=SEAT_TYPE.get(row["seat_type"]),
        flight_class=FLIGHT_CLASS.get(row["flight_class"]),
        flight_reason=FLIGHT_REASON.get(row["flight_reason"]),
        note=row["note"],
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/flights", response_model=list[Flight], summary="List flights")
def list_flights(
    airline: Optional[str] = Query(None, description="Filter by airline name"),
    aircraft: Optional[str] = Query(None, description="Filter by aircraft type"),
    from_airport: Optional[str] = Query(None, description="Filter by departure airport"),
    to_airport: Optional[str] = Query(None, description="Filter by arrival airport"),
    flight_class: Optional[str] = Query(None, description="Economy | Business | First | Premium Economy"),
    flight_reason: Optional[str] = Query(None, description="Personal | Business | Crew"),
    ticket_type: Optional[str] = Query(None, description="revenue | nonrev"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    class_map = {v.lower(): k for k, v in FLIGHT_CLASS.items()}
    reason_map = {v.lower(): k for k, v in FLIGHT_REASON.items()}

    conditions = []
    params = []

    if airline:
        conditions.append("airline ILIKE %s")
        params.append(f"%{airline}%")
    if aircraft:
        conditions.append("aircraft ILIKE %s")
        params.append(f"%{aircraft}%")
    if from_airport:
        conditions.append("from_airport ILIKE %s")
        params.append(f"%{from_airport}%")
    if to_airport:
        conditions.append("to_airport ILIKE %s")
        params.append(f"%{to_airport}%")
    if flight_class:
        code = class_map.get(flight_class.lower())
        if code:
            conditions.append("flight_class = %s")
            params.append(code)
    if flight_reason:
        code = reason_map.get(flight_reason.lower())
        if code:
            conditions.append("flight_reason = %s")
            params.append(code)
    if ticket_type == "nonrev":
        conditions.append("note ILIKE %s")
        params.append("%nonrev%")
    elif ticket_type == "revenue":
        conditions.append("(note NOT ILIKE %s OR note IS NULL)")
        params.append("%nonrev%")
    if date_from:
        conditions.append("date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("date <= %s")
        params.append(date_to)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]

    sql = f"""
        SELECT * FROM flight_diary
        {where}
        ORDER BY date DESC, dep_time DESC
        LIMIT %s OFFSET %s
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return [row_to_flight(dict(r)) for r in cur.fetchall()]


@app.get("/flights/{flight_id}", response_model=Flight, summary="Get a single flight")
def get_flight(flight_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM flight_diary WHERE id = %s", (flight_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Flight not found")
    return row_to_flight(dict(row))


@app.get("/stats", response_model=Stats, summary="Summary statistics")
def get_stats():
    sql = """
        SELECT
            COUNT(*)                                            AS total_flights,
            COALESCE(SUM(EXTRACT(EPOCH FROM duration) / 3600), 0) AS total_hours,
            COUNT(DISTINCT airline)                             AS unique_airlines,
            COUNT(DISTINCT from_airport) + COUNT(DISTINCT to_airport) AS unique_airports
        FROM flight_diary
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        row = dict(cur.fetchone())
    return Stats(
        total_flights=row["total_flights"],
        total_hours=round(float(row["total_hours"]), 1),
        unique_airlines=row["unique_airlines"],
        unique_airports=row["unique_airports"],
    )


@app.get("/aircraft", response_model=list[AircraftSummary], summary="Aircraft types flown")
def list_aircraft():
    sql = """
        SELECT
            aircraft,
            COUNT(*)                                                AS flights,
            COALESCE(SUM(EXTRACT(EPOCH FROM duration) / 3600), 0)  AS total_hours,
            ARRAY_AGG(DISTINCT airline)                             AS airlines
        FROM flight_diary
        WHERE aircraft IS NOT NULL AND TRIM(aircraft) != '()'
        GROUP BY aircraft
        ORDER BY flights DESC
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [
        AircraftSummary(
            aircraft=r["aircraft"],
            flights=r["flights"],
            total_hours=round(float(r["total_hours"]), 1),
            airlines=sorted(r["airlines"]),
        )
        for r in rows
    ]


@app.get("/airports", response_model=list[AirportSummary], summary="Airports visited")
def list_airports():
    try:
        import airportsdata
        import re
        ap_db = airportsdata.load("IATA")
    except ImportError:
        ap_db = {}

    def extract_iata(s):
        m = re.search(r'\(([A-Z]{3})/', str(s))
        return m.group(1) if m else None

    sql = """
        SELECT
            from_airport,
            to_airport,
            COUNT(*) AS flights
        FROM flight_diary
        GROUP BY from_airport, to_airport
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    departures: dict[str, int] = {}
    arrivals: dict[str, int] = {}
    raw_label: dict[str, str] = {}

    for r in rows:
        dep = extract_iata(r["from_airport"])
        arr = extract_iata(r["to_airport"])
        if dep:
            departures[dep] = departures.get(dep, 0) + r["flights"]
            raw_label[dep] = r["from_airport"]
        if arr:
            arrivals[arr] = arrivals.get(arr, 0) + r["flights"]
            raw_label[arr] = r["to_airport"]

    all_codes = sorted(set(departures) | set(arrivals))
    result = []
    for code in all_codes:
        info = ap_db.get(code, {})
        result.append(AirportSummary(
            code=code,
            name=info.get("name", raw_label.get(code, code)),
            city=info.get("city", ""),
            country=info.get("country", ""),
            departures=departures.get(code, 0),
            arrivals=arrivals.get(code, 0),
            total_visits=departures.get(code, 0) + arrivals.get(code, 0),
        ))

    return sorted(result, key=lambda x: x.total_visits, reverse=True)


@app.get("/registrations/{reg}", response_model=RegistrationDetail, summary="Registration detail")
def get_registration(reg: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM flight_diary WHERE registration ILIKE %s ORDER BY date DESC",
            (reg,),
        )
        rows = cur.fetchall()

    flights = [row_to_flight(dict(r)) for r in rows]

    raw = fetch_registration(reg)
    meta = None
    if raw:
        meta = RegistrationMeta(
            registration=raw.get("registration", reg.upper()),
            manufacturer=raw.get("manufacturer"),
            model=raw.get("type"),
            icao_type=raw.get("icao_type"),
            operator=raw.get("registered_owner"),
            country=raw.get("registered_owner_country_name"),
            mode_s=raw.get("mode_s"),
            photo_url=raw.get("url_photo"),
            photo_thumbnail_url=raw.get("url_photo_thumbnail"),
        )

    return RegistrationDetail(meta=meta, flights=flights)
