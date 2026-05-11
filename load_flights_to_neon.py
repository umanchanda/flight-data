"""
load_flights_to_neon.py
-----------------------
Loads flightdiary CSV into a Neon PostgreSQL database.

Requirements:
    pip install psycopg2-binary pandas

Usage:
    1. Set your Neon connection string below (or via env var).
    2. Run: python load_flights_to_neon.py
"""

import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ─── CONFIG ───────────────────────────────────────────────────────────────────

CSV_PATH = "csv/flightdiary_2026_05_11_04_16.csv"  # path to your CSV file

# Paste your Neon connection string here, or set the env var NEON_DATABASE_URL.
# Format: postgresql://user:password@host/dbname?sslmode=require
NEON_DATABASE_URL = os.getenv(
    "NEON_DATABASE_URL",
    "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

TABLE_NAME = "flight_diary"

# ─── SCHEMA ───────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id              SERIAL PRIMARY KEY,
    date            DATE,
    flight_number   TEXT,
    from_airport    TEXT        NOT NULL,
    to_airport      TEXT        NOT NULL,
    dep_time        TIME,
    arr_time        TIME,
    duration        INTERVAL,
    airline         TEXT        NOT NULL,
    aircraft        TEXT,
    registration    TEXT,
    seat_number     TEXT,
    seat_type       SMALLINT,
    flight_class    SMALLINT,
    flight_reason   SMALLINT,
    note            TEXT,
    dep_id          INTEGER,
    arr_id          INTEGER,
    airline_id      INTEGER,
    aircraft_id     INTEGER
);
"""

# Added after initial table creation — safe to run repeatedly.
ADD_UNIQUE_CONSTRAINT_SQL = f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'flight_diary_unique_flight'
    ) THEN
        ALTER TABLE {TABLE_NAME}
        ADD CONSTRAINT flight_diary_unique_flight
        UNIQUE (date, from_airport, to_airport, dep_time);
    END IF;
END$$;
"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def parse_duration(val):
    """Convert HH:MM:SS string to a Postgres INTERVAL-compatible string."""
    if pd.isna(val) or val == "":
        return None
    parts = str(val).strip().split(":")
    if len(parts) == 3:
        return f"{parts[0]} hours {parts[1]} minutes {parts[2]} seconds"
    return None

def clean(val):
    """Return None for NaN/empty, otherwise the raw value."""
    if pd.isna(val) or val == "":
        return None
    return val

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, dtype=str)  # read everything as str first
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # Build list of row tuples in column order
    rows = []
    for _, r in df.iterrows():
        rows.append((
            clean(r["Date"]),
            clean(r["Flight number"]),
            r["From"],
            r["To"],
            clean(r["Dep time"]),
            clean(r["Arr time"]),
            parse_duration(r["Duration"]),
            r["Airline"],
            clean(r["Aircraft"]),
            clean(r["Registration"]),
            clean(r["Seat number"]),
            int(r["Seat type"])    if pd.notna(r["Seat type"])    else None,
            int(r["Flight class"]) if pd.notna(r["Flight class"]) else None,
            int(r["Flight reason"])if pd.notna(r["Flight reason"])else None,
            clean(r["Note"]),
            int(r["Dep_id"])       if pd.notna(r["Dep_id"])       else None,
            int(r["Arr_id"])       if pd.notna(r["Arr_id"])       else None,
            int(r["Airline_id"])   if pd.notna(r["Airline_id"])   else None,
            int(r["Aircraft_id"])  if pd.notna(r["Aircraft_id"])  else None,
        ))

    UPSERT_SQL = f"""
        INSERT INTO {TABLE_NAME} (
            date, flight_number, from_airport, to_airport,
            dep_time, arr_time, duration,
            airline, aircraft, registration,
            seat_number, seat_type, flight_class, flight_reason,
            note, dep_id, arr_id, airline_id, aircraft_id
        ) VALUES %s
        ON CONFLICT (date, from_airport, to_airport, dep_time) DO UPDATE SET
            flight_number = EXCLUDED.flight_number,
            arr_time      = EXCLUDED.arr_time,
            duration      = EXCLUDED.duration,
            airline       = EXCLUDED.airline,
            aircraft      = EXCLUDED.aircraft,
            registration  = EXCLUDED.registration,
            seat_number   = EXCLUDED.seat_number,
            seat_type     = EXCLUDED.seat_type,
            flight_class  = EXCLUDED.flight_class,
            flight_reason = EXCLUDED.flight_reason,
            note          = EXCLUDED.note,
            dep_id        = EXCLUDED.dep_id,
            arr_id        = EXCLUDED.arr_id,
            airline_id    = EXCLUDED.airline_id,
            aircraft_id   = EXCLUDED.aircraft_id
    """

    print(f"\nConnecting to Neon...")
    conn = psycopg2.connect(NEON_DATABASE_URL)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            print(f"Creating table '{TABLE_NAME}' if it doesn't exist...")
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(ADD_UNIQUE_CONSTRAINT_SQL)

            print(f"Upserting {len(rows)} rows...")
            execute_values(cur, UPSERT_SQL, rows, page_size=100)

        conn.commit()
        print(f"\n✅ Done! {len(rows)} rows upserted into '{TABLE_NAME}'.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error — transaction rolled back.")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    main()
