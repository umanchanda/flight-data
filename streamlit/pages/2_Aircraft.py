import os
import sys
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from api_client import load_aircraft, load_flights

st.set_page_config(page_title="Aircraft", page_icon="🛩️", layout="wide")
st.title("🛩️ Aircraft")

df = load_flights()
aircraft_catalog = {
    item["aircraft"]: item.get("specifications")
    for item in load_aircraft()
}
known = sorted(aircraft_catalog)

sel = st.selectbox("Select an aircraft", known)
if not sel:
    st.stop()

specs = aircraft_catalog.get(sel)
flights_on_type = df[df["aircraft"] == sel]

# ── Overview ───────────────────────────────────────────────────────────────────
st.subheader(sel)
if specs:
    st.caption(specs["intro"])

st.divider()

# ── Specs + personal stats side by side ───────────────────────────────────────
left, right = st.columns(2)

with left:
    st.markdown("**Specifications**")
    if specs:
        rows = {
            "Manufacturer": specs["manufacturer"],
            "Family": specs["family"],
            "Type": specs["type"],
            "Engines": specs["engines"],
            "Range": f"{specs['range_km']:,} km",
            "Capacity": f"{specs['capacity']} seats",
            "Wingspan": f"{specs['wingspan_m']} m",
            "Length": f"{specs['length_m']} m",
            "Max speed": f"{specs['max_speed_kmh']} km/h",
            "First flight": specs["first_flight"],
        }
        st.table(pd.DataFrame(rows.items(), columns=["", "Value"]).set_index(""))
    else:
        st.info("No spec data available for this aircraft.")

with right:
    st.markdown("**Your stats on this type**")
    total = len(flights_on_type)
    hours = flights_on_type["duration_hrs"].sum()
    airlines = flights_on_type["airline"].nunique()
    st.metric("Flights", total)
    st.metric("Hours flown", f"{hours:,.1f} h")
    st.metric("Airlines flown with", airlines)

st.divider()

# ── Airlines flown with ────────────────────────────────────────────────────────
st.subheader("Airlines flown with")
airline_counts = flights_on_type["airline"].value_counts().reset_index()
airline_counts.columns = ["Airline", "Flights"]
st.dataframe(airline_counts, hide_index=True, use_container_width=True)

# ── Routes ────────────────────────────────────────────────────────────────────
st.subheader("Routes flown")
routes = (
    flights_on_type
    .groupby(["from_airport", "to_airport"])
    .size()
    .reset_index(name="Flights")
    .sort_values("Flights", ascending=False)
)
routes["Route"] = routes["from_airport"] + " → " + routes["to_airport"]
st.dataframe(routes[["Route", "Flights"]], hide_index=True, use_container_width=True)
