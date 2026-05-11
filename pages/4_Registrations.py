import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from registration_lookup import fetch_registration

load_dotenv()

st.set_page_config(page_title="Registrations", page_icon="🔍", layout="wide")
st.title("🔍 Registrations")


@st.cache_data(ttl=60)
def load_flights() -> pd.DataFrame:
    engine = create_engine(os.environ["NEON_DATABASE_URL"])
    df = pd.read_sql(
        """
        SELECT date, flight_number, from_airport, to_airport,
               airline, aircraft, registration, duration
        FROM flight_diary
        WHERE registration IS NOT NULL
        ORDER BY date DESC
        """,
        engine,
    )
    df["date"] = pd.to_datetime(df["date"])
    df["duration_hrs"] = df["duration"].apply(
        lambda x: round(x.total_seconds() / 3600, 2) if x is not None else None
    )
    return df.drop(columns=["duration"])


@st.cache_data(ttl=3600)
def lookup(reg: str):
    return fetch_registration(reg)


df = load_flights()
registrations = sorted(df["registration"].dropna().unique())

sel_reg = st.selectbox("Select a registration", registrations)
if not sel_reg:
    st.stop()

flights = df[df["registration"] == sel_reg].reset_index(drop=True)
meta = lookup(sel_reg)

st.divider()

# ── Aircraft metadata ──────────────────────────────────────────────────────────
col_info, col_photo = st.columns([2, 1])

with col_info:
    st.subheader(sel_reg)
    if meta:
        rows = {
            "Operator": meta.get("registered_owner", "—"),
            "Manufacturer": meta.get("manufacturer", "—"),
            "Model": meta.get("type", "—"),
            "ICAO type": meta.get("icao_type", "—"),
            "Country": meta.get("registered_owner_country_name", "—"),
            "Mode-S (hex)": meta.get("mode_s", "—"),
        }
        st.table(pd.DataFrame(rows.items(), columns=["", "Value"]).set_index(""))
    else:
        st.info("No external data found for this registration.")

with col_photo:
    if meta and meta.get("url_photo"):
        st.image(meta["url_photo"], caption="© airport-data.com", use_container_width=True)

st.divider()

# ── Personal stats ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Flights on this aircraft", len(flights))
c2.metric("Hours flown", f"{flights['duration_hrs'].sum():,.1f} h")
c3.metric("First flight", flights["date"].min().strftime("%b %d, %Y") if len(flights) else "—")
c4.metric("Last flight", flights["date"].max().strftime("%b %d, %Y") if len(flights) else "—")

st.divider()

# ── Flight history ─────────────────────────────────────────────────────────────
st.subheader("Flight history on this aircraft")
st.dataframe(
    flights.drop(columns=["registration"]),
    hide_index=True,
    width="stretch",
    column_config={
        "date": st.column_config.DateColumn("Date"),
        "flight_number": "Flight #",
        "from_airport": "From",
        "to_airport": "To",
        "airline": "Airline",
        "aircraft": "Aircraft type",
        "duration_hrs": st.column_config.NumberColumn("Duration (h)", format="%.1f"),
    },
)
