from collections import Counter, defaultdict
from datetime import date, time

from fastapi import APIRouter, Query

from ..db import FLIGHT_CLASS, FLIGHT_REASON, SEAT_TYPE, build_flight_where, duration_to_hours, get_conn, normalize_aircraft_name, row_to_flight
from ..models import CountPoint, DashboardCharts, DashboardData, DashboardFilters, FloatPoint, RepeatAircraft, RepeatFlight, RouteCount, Stats

router = APIRouter()


@router.get('/dashboard', response_model=DashboardData, summary='Dashboard data')
def get_dashboard(
    year: list[int] | None = Query(None, description='Filter by year'),
    airline: list[str] | None = Query(None, description='Filter by airline name'),
    aircraft: list[str] | None = Query(None, description='Filter by aircraft type'),
    from_airport: list[str] | None = Query(None, description='Filter by departure airport'),
    to_airport: list[str] | None = Query(None, description='Filter by arrival airport'),
    seat_type: list[str] | None = Query(None, description='Window | Middle | Aisle'),
    flight_class: list[str] | None = Query(None, description='Economy | Business | First | Premium Economy'),
    flight_reason: list[str] | None = Query(None, description='Personal | Business | Crew'),
    ticket_type: str | None = Query(None, description='revenue | nonrev'),
    date_from: date | None = Query(None, description='Start date (YYYY-MM-DD)'),
    date_to: date | None = Query(None, description='End date (YYYY-MM-DD)'),
):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT date, from_airport, to_airport, airline, aircraft, seat_type, flight_class, flight_reason
            FROM flight_diary
            ORDER BY date DESC, dep_time DESC
            """
        )
        option_rows = cur.fetchall()

        where, params = build_flight_where(
            years=year,
            airlines=airline,
            aircraft=aircraft,
            from_airports=from_airport,
            to_airports=to_airport,
            seat_types=seat_type,
            flight_classes=flight_class,
            flight_reasons=flight_reason,
            ticket_type=ticket_type,
            date_from=date_from,
            date_to=date_to,
        )
        cur.execute(
            f"""
            SELECT * FROM flight_diary
            {where}
            ORDER BY date DESC, dep_time DESC
            """,
            params,
        )
        rows = [dict(row) for row in cur.fetchall()]

    flights = [row_to_flight(row) for row in rows]
    total_hours = round(sum(duration_to_hours(row['duration']) for row in rows), 1)
    unique_airports = len(
        {row['from_airport'] for row in rows if row['from_airport']}
        | {row['to_airport'] for row in rows if row['to_airport']}
    )

    flights_by_airline_counter = Counter(row['airline'] for row in rows if row['airline'])
    flights_per_year_counter = Counter(row['date'].year for row in rows if row['date'])
    top_routes_counter = Counter(
        f"{row['from_airport']} → {row['to_airport']}" for row in rows if row['from_airport'] and row['to_airport']
    )
    hours_by_airline_counter: defaultdict[str, float] = defaultdict(float)
    repeat_rows: defaultdict[str, list[dict]] = defaultdict(list)

    for row in rows:
        if row['airline']:
            hours_by_airline_counter[row['airline']] += duration_to_hours(row['duration'])
        if row['registration']:
            repeat_rows[row['registration']].append(row)

    repeat_aircraft = []
    for registration, history_rows in sorted(
        repeat_rows.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        if len(history_rows) < 2:
            continue
        history = [
            RepeatFlight(
                date=row['date'],
                flight_number=row['flight_number'],
                from_airport=row['from_airport'],
                to_airport=row['to_airport'],
                airline=row['airline'],
                aircraft=normalize_aircraft_name(row['aircraft']),
            )
            for row in sorted(
                history_rows,
                key=lambda item: (item['date'] or date.min, item['dep_time'] or time.min),
            )
        ]
        repeat_aircraft.append(
            RepeatAircraft(registration=registration, flights=len(history), history=history)
        )

    filters = DashboardFilters(
        years=sorted({row['date'].year for row in option_rows if row['date']}, reverse=True),
        airlines=sorted({row['airline'] for row in option_rows if row['airline']}),
        airports=sorted(
            {row['from_airport'] for row in option_rows if row['from_airport']}
            | {row['to_airport'] for row in option_rows if row['to_airport']}
        ),
        classes=sorted(FLIGHT_CLASS.values()),
        aircraft=sorted(
            {
                normalized
                for row in option_rows
                if (normalized := normalize_aircraft_name(row['aircraft']))
            }
        ),
        seat_types=sorted(SEAT_TYPE.values()),
        reasons=sorted(FLIGHT_REASON.values()),
        date_min=min((row['date'] for row in option_rows if row['date']), default=None),
        date_max=max((row['date'] for row in option_rows if row['date']), default=None),
    )

    return DashboardData(
        summary=Stats(
            total_flights=len(rows),
            total_hours=total_hours,
            unique_airlines=len({row['airline'] for row in rows if row['airline']}),
            unique_airports=unique_airports,
        ),
        filters=filters,
        flights=flights,
        charts=DashboardCharts(
            flights_by_airline=[
                CountPoint(label=label, value=value)
                for label, value in flights_by_airline_counter.most_common()
            ],
            flights_per_year=[
                CountPoint(label=str(label), value=value)
                for label, value in sorted(flights_per_year_counter.items())
            ],
            top_routes=[
                RouteCount(route=label, count=value)
                for label, value in top_routes_counter.most_common(10)
            ],
            hours_by_airline=[
                FloatPoint(label=label, value=round(value, 1))
                for label, value in sorted(
                    hours_by_airline_counter.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        ),
        repeat_aircraft=repeat_aircraft,
    )
