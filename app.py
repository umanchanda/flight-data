import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

SEAT_TYPE = {1: "Window", 2: "Middle", 3: "Aisle"}
FLIGHT_CLASS = {1: "Economy", 3: "Premium Economy", 2: "Business", 4: "First"}
FLIGHT_REASON = {1: "Personal", 2: "Business", 3: "Crew"}

st.set_page_config(page_title="Flight Diary", page_icon="✈️", layout="wide")
st.title("✈️ Flight Diary")


@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    engine = create_engine(os.environ["NEON_DATABASE_URL"])
    df = pd.read_sql(
        """
        SELECT
            date, flight_number, from_airport, to_airport,
            dep_time, arr_time, duration,
            airline, aircraft, registration,
            seat_number, seat_type, flight_class, flight_reason, note
        FROM flight_diary
        ORDER BY date DESC, dep_time DESC
        """,
        engine,
    )
    df["date"] = pd.to_datetime(df["date"])
    df["aircraft"] = df["aircraft"].str.strip().replace("()", None)
    df["seat_type"] = df["seat_type"].map(SEAT_TYPE)
    df["flight_class"] = df["flight_class"].map(FLIGHT_CLASS)
    df["flight_reason"] = df["flight_reason"].map(FLIGHT_REASON)
    df["duration_hrs"] = df["duration"].apply(
        lambda x: round(x.total_seconds() / 3600, 2) if x is not None else None
    )
    return df


df = load_data()

# ── Summary metrics ────────────────────────────────────────────────────────────
total_flights = len(df)
total_hours = df["duration_hrs"].sum()
unique_airlines = df["airline"].nunique()
unique_airports = pd.concat([df["from_airport"], df["to_airport"]]).nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Flights", total_flights)
c2.metric("Total Hours Flown", f"{total_hours:,.1f} h")
c3.metric("Airlines", unique_airlines)
c4.metric("Airports Visited", unique_airports)

st.divider()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    years = sorted(df["date"].dt.year.dropna().unique().astype(int), reverse=True)
    sel_years = st.multiselect("Year", years)

    airlines = sorted(df["airline"].dropna().unique())
    sel_airlines = st.multiselect("Airline", airlines)

    airports = sorted(pd.concat([df["from_airport"], df["to_airport"]]).dropna().unique())
    sel_from = st.multiselect("From airport", airports)
    sel_to = st.multiselect("To airport", airports)

    classes = sorted(df["flight_class"].dropna().unique())
    sel_class = st.multiselect("Class", classes)

    aircraft_types = sorted(df["aircraft"].dropna().unique())
    sel_aircraft = st.multiselect("Aircraft type", aircraft_types)

    seat_types = sorted(df["seat_type"].dropna().unique())
    sel_seat_type = st.multiselect("Seat type", seat_types)

    reasons = sorted(df["flight_reason"].dropna().unique())
    sel_reason = st.multiselect("Flight reason", reasons)

    sel_ticket_type = st.radio(
        "Ticket type",
        options=["All", "Revenue", "Nonrev"],
        index=0,
        horizontal=True,
    )

    date_min = df["date"].min()
    date_max = df["date"].max()
    sel_dates = st.date_input("Date range", value=(date_min, date_max))

filtered = df.copy()
if sel_years:
    filtered = filtered[filtered["date"].dt.year.isin(sel_years)]
if sel_airlines:
    filtered = filtered[filtered["airline"].isin(sel_airlines)]
if sel_from:
    filtered = filtered[filtered["from_airport"].isin(sel_from)]
if sel_to:
    filtered = filtered[filtered["to_airport"].isin(sel_to)]
if sel_class:
    filtered = filtered[filtered["flight_class"].isin(sel_class)]
if sel_aircraft:
    filtered = filtered[filtered["aircraft"].isin(sel_aircraft)]
if sel_seat_type:
    filtered = filtered[filtered["seat_type"].isin(sel_seat_type)]
if sel_reason:
    filtered = filtered[filtered["flight_reason"].isin(sel_reason)]
if sel_ticket_type == "Nonrev":
    filtered = filtered[filtered["note"].str.contains("nonrev", case=False, na=False)]
elif sel_ticket_type == "Revenue":
    filtered = filtered[~filtered["note"].str.contains("nonrev", case=False, na=False)]
if isinstance(sel_dates, (list, tuple)) and len(sel_dates) == 2:
    filtered = filtered[
        (filtered["date"] >= pd.Timestamp(sel_dates[0]))
        & (filtered["date"] <= pd.Timestamp(sel_dates[1]))
    ]

# ── Flight table ───────────────────────────────────────────────────────────────
st.subheader(f"Flights ({len(filtered)})")
st.dataframe(
    filtered.drop(columns=["duration"]),
    width="stretch",
    hide_index=True,
    column_config={
        "date": st.column_config.DateColumn("Date"),
        "flight_number": "Flight #",
        "from_airport": "From",
        "to_airport": "To",
        "dep_time": "Dep",
        "arr_time": "Arr",
        "duration_hrs": st.column_config.NumberColumn("Duration (h)", format="%.1f"),
        "airline": "Airline",
        "aircraft": "Aircraft",
        "registration": "Reg",
        "seat_number": "Seat",
        "seat_type": "Seat Type",
        "flight_class": "Class",
        "flight_reason": "Reason",
        "note": "Note",
    },
)

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Flights by Airline")
    airline_counts = filtered["airline"].value_counts().reset_index()
    airline_counts.columns = ["airline", "flights"]
    st.bar_chart(airline_counts.set_index("airline"))

with col2:
    st.subheader("Flights per Year")
    filtered["year"] = pd.to_datetime(filtered["date"]).dt.year
    year_counts = filtered.groupby("year").size().reset_index(name="flights")
    st.bar_chart(year_counts.set_index("year"))

col3, col4 = st.columns(2)

with col3:
    st.subheader("Top Routes")
    routes = (
        filtered.groupby(["from_airport", "to_airport"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(10)
    )
    routes["route"] = routes["from_airport"] + " → " + routes["to_airport"]
    st.bar_chart(routes.set_index("route")["count"])

with col4:
    st.subheader("Hours by Airline")
    hours_by_airline = (
        filtered.groupby("airline")["duration_hrs"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.bar_chart(hours_by_airline.set_index("airline"))
