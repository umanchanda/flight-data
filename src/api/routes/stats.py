from fastapi import APIRouter

from ..db import get_conn
from ..models import Stats

router = APIRouter()


@router.get("/stats", response_model=Stats, summary="Summary statistics")
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
