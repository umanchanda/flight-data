from fastapi import APIRouter

from registration_lookup import fetch_registration
from ..db import get_conn, row_to_flight
from ..models import Flight, RegistrationDetail, RegistrationMeta

router = APIRouter()


@router.get("/registrations/{reg}", response_model=RegistrationDetail, summary="Registration detail")
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
