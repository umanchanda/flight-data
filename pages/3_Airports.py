import os
import re
import pandas as pd
import streamlit as st
import airportsdata
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.set_page_config(page_title="Airports", page_icon="🗺️", layout="wide")
st.title("🗺️ Airports")

AIRPORTS = airportsdata.load("IATA")

def extract_iata(code_str: str) -> str | None:
    m = re.search(r'\(([A-Z]{3})/', str(code_str))
    return m.group(1) if m else None

def display_name(code_str: str) -> str:
    # "Los Angeles / Los Angeles International (LAX/KLAX)" → "Los Angeles International (LAX)"
    iata = extract_iata(code_str)
    info = AIRPORTS.get(iata) if iata else None
    if info:
        return f"{info['name']} ({iata})"
    return code_str


@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    engine = create_engine(os.environ["NEON_DATABASE_URL"])
    df = pd.read_sql(
        "SELECT date, from_airport, to_airport, airline, aircraft FROM flight_diary",
        engine,
    )
    df["date"] = pd.to_datetime(df["date"])
    df["from_iata"] = df["from_airport"].map(extract_iata)
    df["to_iata"] = df["to_airport"].map(extract_iata)
    return df


df = load_data()

all_iata = sorted(
    set(df["from_iata"].dropna()) | set(df["to_iata"].dropna())
)

# ── Map of all visited airports ────────────────────────────────────────────────
st.subheader(f"Airports visited: {len(all_iata)}")

map_rows = []
for code in all_iata:
    info = AIRPORTS.get(code)
    if info:
        visits = (
            (df["from_iata"] == code).sum() + (df["to_iata"] == code).sum()
        )
        map_rows.append({"lat": info["lat"], "lon": info["lon"], "iata": code, "visits": visits})

map_df = pd.DataFrame(map_rows)
if not map_df.empty:
    st.map(map_df, size="visits", zoom=2)

st.divider()

# ── Airport detail ─────────────────────────────────────────────────────────────
st.subheader("Airport detail")

options = sorted(all_iata, key=lambda c: AIRPORTS.get(c, {}).get("name", c))
labels = {c: display_name(df[df["from_iata"] == c]["from_airport"].iloc[0]
                          if (df["from_iata"] == c).any()
                          else df[df["to_iata"] == c]["to_airport"].iloc[0])
          for c in options}

sel_iata = st.selectbox(
    "Select an airport",
    options,
    format_func=lambda c: labels[c],
)
if not sel_iata:
    st.stop()

info = AIRPORTS.get(sel_iata, {})
arrivals = df[df["to_iata"] == sel_iata]
departures = df[df["from_iata"] == sel_iata]
all_visits = pd.concat([arrivals, departures])

col_info, col_stats = st.columns(2)

with col_info:
    st.markdown("**Airport info**")
    if info:
        rows = {
            "Name": info.get("name", "—"),
            "City": info.get("city", "—"),
            "State / Region": info.get("subd", "—"),
            "Country": info.get("country", "—"),
            "IATA": sel_iata,
            "ICAO": info.get("icao", "—"),
            "Elevation": f"{info['elevation']:.0f} ft" if info.get("elevation") is not None else "—",
            "Timezone": info.get("tz", "—"),
        }
        st.table(pd.DataFrame(rows.items(), columns=["", "Value"]).set_index(""))
    else:
        st.info("No info available for this airport.")

with col_stats:
    st.markdown("**Your stats**")
    st.metric("Total visits", len(all_visits))
    st.metric("Departures", len(departures))
    st.metric("Arrivals", len(arrivals))
    if not all_visits.empty:
        st.metric("First visit", all_visits["date"].min().strftime("%b %d, %Y"))
        st.metric("Last visit", all_visits["date"].max().strftime("%b %d, %Y"))

st.divider()

col_dep, col_arr = st.columns(2)

with col_dep:
    st.subheader("Destinations from here")
    if not departures.empty:
        dest = (
            departures.groupby("to_airport")
            .size()
            .reset_index(name="Flights")
            .sort_values("Flights", ascending=False)
        )
        dest["Destination"] = dest["to_airport"].apply(display_name)
        st.dataframe(dest[["Destination", "Flights"]], hide_index=True, width="stretch")
    else:
        st.caption("No departures recorded.")

with col_arr:
    st.subheader("Origins into here")
    if not arrivals.empty:
        orig = (
            arrivals.groupby("from_airport")
            .size()
            .reset_index(name="Flights")
            .sort_values("Flights", ascending=False)
        )
        orig["Origin"] = orig["from_airport"].apply(display_name)
        st.dataframe(orig[["Origin", "Flights"]], hide_index=True, width="stretch")
    else:
        st.caption("No arrivals recorded.")

st.subheader("Airlines used here")
if not all_visits.empty:
    airline_counts = (
        all_visits["airline"].value_counts().reset_index()
    )
    airline_counts.columns = ["Airline", "Flights"]
    st.dataframe(airline_counts, hide_index=True, width="stretch")
