from fastapi import APIRouter

from ..db import get_conn
from ..models import AircraftSummary

router = APIRouter()


@router.get("/aircraft", response_model=list[AircraftSummary], summary="Aircraft types flown")
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
