from collections import defaultdict
import re

from fastapi import APIRouter, HTTPException

from ..db import get_conn
from ..models import AirlineFlights, AirportDetail, AirportInfo, AirportRouteCount, AirportStatsDetail, AirportSummary

router = APIRouter()


def _extract_iata(value: str | None) -> str | None:
    match = re.search(r'\(([A-Z]{3})/', str(value))
    return match.group(1) if match else None


def _display_name(code: str, raw_label: str | None, ap_db: dict) -> str:
    info = ap_db.get(code)
    if info:
        return f"{info['name']} ({code})"
    return raw_label or code


def _load_airport_rows():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT date, from_airport, to_airport, airline
            FROM flight_diary
            ORDER BY date DESC, dep_time DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]


def _load_airport_db():
    try:
        import airportsdata

        return airportsdata.load('IATA')
    except ImportError:
        return {}


@router.get('/airports', response_model=list[AirportSummary], summary='Airports visited')
def list_airports():
    rows = _load_airport_rows()
    ap_db = _load_airport_db()
    departures: defaultdict[str, int] = defaultdict(int)
    arrivals: defaultdict[str, int] = defaultdict(int)
    raw_labels: dict[str, str] = {}

    for row in rows:
        dep = _extract_iata(row['from_airport'])
        arr = _extract_iata(row['to_airport'])
        if dep:
            departures[dep] += 1
            raw_labels[dep] = row['from_airport']
        if arr:
            arrivals[arr] += 1
            raw_labels[arr] = row['to_airport']

    result = []
    for code in sorted(set(departures) | set(arrivals)):
        info = ap_db.get(code, {})
        result.append(
            AirportSummary(
                code=code,
                name=info.get('name', raw_labels.get(code, code)),
                city=info.get('city', ''),
                country=info.get('country', ''),
                departures=departures.get(code, 0),
                arrivals=arrivals.get(code, 0),
                total_visits=departures.get(code, 0) + arrivals.get(code, 0),
                lat=info.get('lat'),
                lon=info.get('lon'),
            )
        )

    return sorted(result, key=lambda item: (-item.total_visits, item.code))


@router.get('/airports/{code}', response_model=AirportDetail, summary='Airport detail')
def get_airport(code: str):
    selected_code = code.upper()
    rows = _load_airport_rows()
    ap_db = _load_airport_db()
    departures = [row for row in rows if _extract_iata(row['from_airport']) == selected_code]
    arrivals = [row for row in rows if _extract_iata(row['to_airport']) == selected_code]
    visits = arrivals + departures
    if not visits:
        raise HTTPException(status_code=404, detail='Airport not found')

    info = ap_db.get(selected_code, {})
    destination_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    origin_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    airline_counts: defaultdict[str, int] = defaultdict(int)

    for row in departures:
        destination_code = _extract_iata(row['to_airport']) or row['to_airport']
        destination_counts[(destination_code, row['to_airport'])] += 1
    for row in arrivals:
        origin_code = _extract_iata(row['from_airport']) or row['from_airport']
        origin_counts[(origin_code, row['from_airport'])] += 1
    for row in visits:
        airline_counts[row['airline']] += 1

    return AirportDetail(
        info=AirportInfo(
            name=info.get('name', _display_name(selected_code, None, ap_db)),
            city=info.get('city', ''),
            state_region=info.get('subd', ''),
            country=info.get('country', ''),
            iata=selected_code,
            icao=info.get('icao', ''),
            elevation_ft=info.get('elevation'),
            timezone=info.get('tz', ''),
            lat=info.get('lat'),
            lon=info.get('lon'),
        ),
        stats=AirportStatsDetail(
            total_visits=len(visits),
            departures=len(departures),
            arrivals=len(arrivals),
            first_visit=min((row['date'] for row in visits if row['date']), default=None),
            last_visit=max((row['date'] for row in visits if row['date']), default=None),
        ),
        destinations=[
            AirportRouteCount(
                airport=airport,
                label=_display_name(airport, raw_label, ap_db),
                flights=flights,
            )
            for (airport, raw_label), flights in sorted(
                destination_counts.items(),
                key=lambda item: (-item[1], item[0][0]),
            )
        ],
        origins=[
            AirportRouteCount(
                airport=airport,
                label=_display_name(airport, raw_label, ap_db),
                flights=flights,
            )
            for (airport, raw_label), flights in sorted(
                origin_counts.items(),
                key=lambda item: (-item[1], item[0][0]),
            )
        ],
        airlines=[
            AirlineFlights(airline=airline, flights=flights)
            for airline, flights in sorted(
                airline_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )
