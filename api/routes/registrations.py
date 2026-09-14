from fastapi import APIRouter, HTTPException

from registration_lookup import fetch_photo, fetch_registration

from ..db import duration_to_hours, get_conn, normalize_aircraft_name, row_to_flight
from ..models import RegistrationDetail, RegistrationListItem, RegistrationMeta, RegistrationPhoto, RegistrationStats

router = APIRouter()


def _normalize_photo(photo: dict | None) -> RegistrationPhoto | None:
    if not photo:
        return None
    url = photo.get('url')
    if isinstance(url, str) and url.strip():
        normalized = f'https:{url}' if url.startswith('//') else url
    elif isinstance(url, dict):
        nested = url.get('src') or url.get('url')
        if not isinstance(nested, str) or not nested.strip():
            return None
        normalized = f'https:{nested}' if nested.startswith('//') else nested
    else:
        return None
    return RegistrationPhoto(
        url=normalized,
        photographer=photo.get('photographer'),
        link=photo.get('link'),
    )


@router.get('/registrations', response_model=list[RegistrationListItem], summary='Registrations flown')
def list_registrations():
    sql = """
        SELECT registration, COUNT(*) AS flights, MAX(aircraft) AS aircraft
        FROM flight_diary
        WHERE registration IS NOT NULL
        GROUP BY registration
        ORDER BY registration ASC
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [
        RegistrationListItem(
            registration=row['registration'],
            flights=row['flights'],
            aircraft=normalize_aircraft_name(row['aircraft']),
        )
        for row in rows
    ]


@router.get('/registrations/{reg}', response_model=RegistrationDetail, summary='Registration detail')
def get_registration(reg: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            'SELECT * FROM flight_diary WHERE registration ILIKE %s ORDER BY date DESC, dep_time DESC',
            (reg,),
        )
        rows = [dict(row) for row in cur.fetchall()]

    if not rows:
        raise HTTPException(status_code=404, detail='Registration not found')

    raw = fetch_registration(reg)
    photo = _normalize_photo(fetch_photo(reg))
    meta = None
    if raw or photo:
        meta = RegistrationMeta(
            registration=(raw or {}).get('registration', reg.upper()),
            manufacturer=(raw or {}).get('manufacturer'),
            model=(raw or {}).get('type'),
            icao_type=(raw or {}).get('icao_type'),
            operator=(raw or {}).get('registered_owner'),
            country=(raw or {}).get('registered_owner_country_name'),
            mode_s=(raw or {}).get('mode_s'),
            photo=photo,
        )

    dates = [row['date'] for row in rows if row['date']]
    return RegistrationDetail(
        meta=meta,
        stats=RegistrationStats(
            total_flights=len(rows),
            total_hours=round(sum(duration_to_hours(row['duration']) for row in rows), 1),
            first_flight=min(dates, default=None),
            last_flight=max(dates, default=None),
        ),
        flights=[row_to_flight(row) for row in rows],
    )
