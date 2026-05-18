from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import get_conn, FLIGHT_CLASS, FLIGHT_REASON, row_to_flight
from ..models import Flight

router = APIRouter()


@router.get("/flights", response_model=list[Flight], summary="List flights")
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


@router.get("/flights/{flight_id}", response_model=Flight, summary="Get a single flight")
def get_flight(flight_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM flight_diary WHERE id = %s", (flight_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Flight not found")
    return row_to_flight(dict(row))
