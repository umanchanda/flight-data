import os

import psycopg2
import psycopg2.extras

SEAT_TYPE = {1: "Window", 2: "Middle", 3: "Aisle"}
FLIGHT_CLASS = {1: "Economy", 3: "Premium Economy", 2: "Business", 4: "First"}
FLIGHT_REASON = {1: "Personal", 2: "Business", 3: "Crew"}


def get_conn():
    return psycopg2.connect(
        os.environ["NEON_DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def row_to_flight(row: dict):
    from .models import Flight
    duration = row["duration"]
    duration_minutes = int(duration.total_seconds() // 60) if duration else None
    return Flight(
        id=row["id"],
        date=row["date"],
        flight_number=row["flight_number"],
        from_airport=row["from_airport"],
        to_airport=row["to_airport"],
        dep_time=row["dep_time"],
        arr_time=row["arr_time"],
        duration_minutes=duration_minutes,
        airline=row["airline"],
        aircraft=row["aircraft"],
        registration=row["registration"],
        seat_number=row["seat_number"],
        seat_type=SEAT_TYPE.get(row["seat_type"]),
        flight_class=FLIGHT_CLASS.get(row["flight_class"]),
        flight_reason=FLIGHT_REASON.get(row["flight_reason"]),
        note=row["note"],
    )
