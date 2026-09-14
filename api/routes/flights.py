from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..db import build_flight_where, get_conn, row_to_flight
from ..models import Flight

router = APIRouter()


@router.get('/flights', response_model=list[Flight], summary='List flights')
def list_flights(
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
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
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
    sql = f"""
        SELECT * FROM flight_diary
        {where}
        ORDER BY date DESC, dep_time DESC
        LIMIT %s OFFSET %s
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, [*params, limit, offset])
        return [row_to_flight(dict(row)) for row in cur.fetchall()]


@router.get('/flights/{flight_id}', response_model=Flight, summary='Get a single flight')
def get_flight(flight_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('SELECT * FROM flight_diary WHERE id = %s', (flight_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Flight not found')
    return row_to_flight(dict(row))
