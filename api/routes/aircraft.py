from collections import defaultdict

from fastapi import APIRouter, HTTPException

from ..aircraft_specs import AIRCRAFT_SPECS
from ..db import duration_to_hours, get_conn, normalize_aircraft_name
from ..models import AircraftDetail, AircraftSpec, AircraftStats, AircraftSummary, AirlineFlights, RouteFlights

router = APIRouter()


def _load_aircraft_rows():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT date, from_airport, to_airport, airline, aircraft, duration
            FROM flight_diary
            WHERE aircraft IS NOT NULL
            ORDER BY date DESC, dep_time DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]


@router.get('/aircraft', response_model=list[AircraftSummary], summary='Aircraft types flown')
def list_aircraft():
    grouped: dict[str, dict] = {}
    for row in _load_aircraft_rows():
        aircraft_name = normalize_aircraft_name(row['aircraft'])
        if not aircraft_name:
            continue
        item = grouped.setdefault(
            aircraft_name,
            {'flights': 0, 'total_hours': 0.0, 'airlines': set()},
        )
        item['flights'] += 1
        item['total_hours'] += duration_to_hours(row['duration'])
        if row['airline']:
            item['airlines'].add(row['airline'])

    return [
        AircraftSummary(
            aircraft=aircraft_name,
            flights=data['flights'],
            total_hours=round(data['total_hours'], 1),
            airlines=sorted(data['airlines']),
        )
        for aircraft_name, data in sorted(
            grouped.items(),
            key=lambda item: (-item[1]['flights'], item[0]),
        )
    ]


@router.get('/aircraft/{aircraft_name}', response_model=AircraftDetail, summary='Aircraft type detail')
def get_aircraft(aircraft_name: str):
    rows = _load_aircraft_rows()
    available_aircraft = sorted(
        {
            normalized
            for row in rows
            if (normalized := normalize_aircraft_name(row['aircraft']))
        }
    )
    flights_on_type = [row for row in rows if normalize_aircraft_name(row['aircraft']) == aircraft_name]
    if not flights_on_type:
        raise HTTPException(status_code=404, detail='Aircraft not found')

    airline_counts: defaultdict[str, int] = defaultdict(int)
    route_counts: defaultdict[str, int] = defaultdict(int)
    total_hours = 0.0
    for row in flights_on_type:
        airline_counts[row['airline']] += 1
        route_counts[f"{row['from_airport']} → {row['to_airport']}"] += 1
        total_hours += duration_to_hours(row['duration'])

    spec_data = AIRCRAFT_SPECS.get(aircraft_name)
    spec = AircraftSpec(**spec_data) if spec_data else None

    return AircraftDetail(
        name=aircraft_name,
        available_aircraft=available_aircraft,
        spec=spec,
        stats=AircraftStats(
            flights=len(flights_on_type),
            total_hours=round(total_hours, 1),
            unique_airlines=len({row['airline'] for row in flights_on_type if row['airline']}),
        ),
        airlines=[
            AirlineFlights(airline=label, flights=value)
            for label, value in sorted(
                airline_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        routes=[
            RouteFlights(route=label, flights=value)
            for label, value in sorted(
                route_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )
