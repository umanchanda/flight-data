import os
from collections.abc import Sequence
from datetime import date

import psycopg2
import psycopg2.extras

SEAT_TYPE = {1: 'Window', 2: 'Middle', 3: 'Aisle'}
FLIGHT_CLASS = {1: 'Economy', 3: 'Premium Economy', 2: 'Business', 4: 'First'}
FLIGHT_REASON = {1: 'Personal', 2: 'Business', 3: 'Crew'}


def get_conn():
    return psycopg2.connect(
        os.environ['NEON_DATABASE_URL'],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def normalize_aircraft_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned == '()':
        return None
    return cleaned


def duration_to_hours(duration) -> float:
    return round(duration.total_seconds() / 3600, 2) if duration else 0.0


def row_to_flight(row: dict):
    from .models import Flight

    duration = row['duration']
    duration_minutes = int(duration.total_seconds() // 60) if duration else None
    return Flight(
        id=row['id'],
        date=row['date'],
        flight_number=row['flight_number'],
        from_airport=row['from_airport'],
        to_airport=row['to_airport'],
        dep_time=row['dep_time'],
        arr_time=row['arr_time'],
        duration_minutes=duration_minutes,
        airline=row['airline'],
        aircraft=normalize_aircraft_name(row['aircraft']),
        registration=row['registration'],
        seat_number=row['seat_number'],
        seat_type=SEAT_TYPE.get(row['seat_type']),
        flight_class=FLIGHT_CLASS.get(row['flight_class']),
        flight_reason=FLIGHT_REASON.get(row['flight_reason']),
        note=row['note'],
    )


def _clean_text_values(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    cleaned = []
    for value in values:
        stripped = value.strip()
        if stripped:
            cleaned.append(stripped)
    return cleaned


def _map_display_values(values: Sequence[str] | None, mapping: dict[int, str]) -> list[int]:
    reverse = {label.lower(): code for code, label in mapping.items()}
    return [reverse[value.lower()] for value in _clean_text_values(values) if value.lower() in reverse]


def build_flight_where(
    *,
    years: Sequence[int] | None = None,
    airlines: Sequence[str] | None = None,
    aircraft: Sequence[str] | None = None,
    from_airports: Sequence[str] | None = None,
    to_airports: Sequence[str] | None = None,
    seat_types: Sequence[str] | None = None,
    flight_classes: Sequence[str] | None = None,
    flight_reasons: Sequence[str] | None = None,
    ticket_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    conditions: list[str] = []
    params: list[object] = []

    if years:
        conditions.append('EXTRACT(YEAR FROM date) = ANY(%s)')
        params.append(sorted({int(year) for year in years}))

    for column, values in (
        ('airline', airlines),
        ('aircraft', aircraft),
        ('from_airport', from_airports),
        ('to_airport', to_airports),
    ):
        cleaned = _clean_text_values(values)
        if cleaned:
            conditions.append(f'{column} ILIKE ANY(%s)')
            params.append([f'%{value}%' for value in cleaned])

    seat_codes = _map_display_values(seat_types, SEAT_TYPE)
    if seat_codes:
        conditions.append('seat_type = ANY(%s)')
        params.append(seat_codes)

    class_codes = _map_display_values(flight_classes, FLIGHT_CLASS)
    if class_codes:
        conditions.append('flight_class = ANY(%s)')
        params.append(class_codes)

    reason_codes = _map_display_values(flight_reasons, FLIGHT_REASON)
    if reason_codes:
        conditions.append('flight_reason = ANY(%s)')
        params.append(reason_codes)

    normalized_ticket_type = (ticket_type or '').strip().lower()
    if normalized_ticket_type == 'nonrev':
        conditions.append('note ILIKE %s')
        params.append('%nonrev%')
    elif normalized_ticket_type == 'revenue':
        conditions.append('(note NOT ILIKE %s OR note IS NULL)')
        params.append('%nonrev%')

    if date_from:
        conditions.append('date >= %s')
        params.append(date_from)
    if date_to:
        conditions.append('date <= %s')
        params.append(date_to)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ''
    return where, params
