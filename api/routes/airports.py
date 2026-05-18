import re

from fastapi import APIRouter

from ..db import get_conn
from ..models import AirportSummary

router = APIRouter()


def _extract_iata(s: str) -> str | None:
    m = re.search(r'\(([A-Z]{3})/', str(s))
    return m.group(1) if m else None


@router.get("/airports", response_model=list[AirportSummary], summary="Airports visited")
def list_airports():
    try:
        import airportsdata
        ap_db = airportsdata.load("IATA")
    except ImportError:
        ap_db = {}

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
        dep = _extract_iata(r["from_airport"])
        arr = _extract_iata(r["to_airport"])
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
