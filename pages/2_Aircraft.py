import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.set_page_config(page_title="Aircraft", page_icon="🛩️", layout="wide")
st.title("🛩️ Aircraft")

AIRCRAFT_SPECS = {
    "Airbus A319 (A319)": {
        "manufacturer": "Airbus",
        "family": "A320 family",
        "type": "Narrow-body",
        "engines": "2× CFM56 or IAE V2500",
        "range_km": 6850,
        "capacity": "124–156",
        "wingspan_m": 33.9,
        "length_m": 33.8,
        "max_speed_kmh": 903,
        "first_flight": "1995",
        "intro": (
            "The A319 is the shortest member of the A320 family, seating up to 156 passengers. "
            "Its range makes it popular for thin routes and secondary city pairs."
        ),
    },
    "Airbus A320-100 (A320)": {
        "manufacturer": "Airbus",
        "family": "A320 family",
        "type": "Narrow-body",
        "engines": "2× CFM56 or IAE V2524",
        "range_km": 5700,
        "capacity": "150–180",
        "wingspan_m": 33.9,
        "length_m": 37.6,
        "max_speed_kmh": 903,
        "first_flight": "1987",
        "intro": (
            "The original A320 was the first commercial aircraft to use fly-by-wire controls. "
            "The -100 was a short production run before the improved -200 took over."
        ),
    },
    "Airbus A320-200 (A320)": {
        "manufacturer": "Airbus",
        "family": "A320 family",
        "type": "Narrow-body",
        "engines": "2× CFM56 or IAE V2500",
        "range_km": 6150,
        "capacity": "150–180",
        "wingspan_m": 33.9,
        "length_m": 37.6,
        "max_speed_kmh": 903,
        "first_flight": "1988",
        "intro": (
            "The A320-200 added winglets and extra fuel capacity over the -100, becoming one of "
            "the best-selling single-aisle jets ever built with over 4,000 delivered."
        ),
    },
    "Airbus A321 (A321)": {
        "manufacturer": "Airbus",
        "family": "A320 family",
        "type": "Narrow-body",
        "engines": "2× CFM56 or IAE V2533",
        "range_km": 5950,
        "capacity": "180–220",
        "wingspan_m": 34.1,
        "length_m": 44.5,
        "max_speed_kmh": 903,
        "first_flight": "1993",
        "intro": (
            "The A321 is the stretched variant of the A320, offering the highest capacity in the "
            "family. It competes directly with the Boeing 757 on medium-haul routes."
        ),
    },
    "Airbus A321neo (A21N)": {
        "manufacturer": "Airbus",
        "family": "A320neo family",
        "type": "Narrow-body",
        "engines": "2× CFM LEAP-1A or PW1100G",
        "range_km": 7400,
        "capacity": "180–220",
        "wingspan_m": 35.8,
        "length_m": 44.5,
        "max_speed_kmh": 903,
        "first_flight": "2016",
        "intro": (
            "The A321neo (New Engine Option) delivers ~20% better fuel efficiency than the ceo. "
            "The XLR variant can fly transatlantic routes non-stop from a single aisle."
        ),
    },
    "Airbus A350-900 (A359)": {
        "manufacturer": "Airbus",
        "family": "A350 XWB",
        "type": "Wide-body",
        "engines": "2× Rolls-Royce Trent XWB-84",
        "range_km": 15000,
        "capacity": "300–440",
        "wingspan_m": 64.8,
        "length_m": 66.8,
        "max_speed_kmh": 945,
        "first_flight": "2013",
        "intro": (
            "The A350-900 is built from 53% composite materials, making it one of the most "
            "fuel-efficient wide-bodies. It directly competes with the Boeing 787 and 777."
        ),
    },
    "Boeing 737 MAX 8 (B38M)": {
        "manufacturer": "Boeing",
        "family": "737 MAX",
        "type": "Narrow-body",
        "engines": "2× CFM LEAP-1B",
        "range_km": 6570,
        "capacity": "162–210",
        "wingspan_m": 35.9,
        "length_m": 39.5,
        "max_speed_kmh": 839,
        "first_flight": "2016",
        "intro": (
            "The 737 MAX 8 is Boeing's best-selling MAX variant. After two fatal accidents led to "
            "a 20-month global grounding (2019–2020), it returned to service with MCAS software updates."
        ),
    },
    "Boeing 737 MAX 9 (B39M)": {
        "manufacturer": "Boeing",
        "family": "737 MAX",
        "type": "Narrow-body",
        "engines": "2× CFM LEAP-1B",
        "range_km": 6570,
        "capacity": "178–220",
        "wingspan_m": 35.9,
        "length_m": 42.2,
        "max_speed_kmh": 839,
        "first_flight": "2017",
        "intro": (
            "The stretched sibling of the MAX 8, the MAX 9 seats up to 220 passengers. "
            "It was briefly grounded in January 2024 after a door plug blowout on an Alaska Airlines flight."
        ),
    },
    "Boeing 737-700 (B737)": {
        "manufacturer": "Boeing",
        "family": "737 Next Generation",
        "type": "Narrow-body",
        "engines": "2× CFM56-7B",
        "range_km": 6370,
        "capacity": "126–149",
        "wingspan_m": 34.3,
        "length_m": 33.6,
        "max_speed_kmh": 839,
        "first_flight": "1997",
        "intro": (
            "The smallest of the 737 NG family, the 737-700 is the backbone of Southwest Airlines. "
            "It replaced the 737-300 and seats around 143 passengers in a typical two-class layout."
        ),
    },
    "Boeing 737-800 (B738)": {
        "manufacturer": "Boeing",
        "family": "737 Next Generation",
        "type": "Narrow-body",
        "engines": "2× CFM56-7B",
        "range_km": 5765,
        "capacity": "162–189",
        "wingspan_m": 35.8,
        "length_m": 39.5,
        "max_speed_kmh": 842,
        "first_flight": "1998",
        "intro": (
            "The 737-800 is one of the most commercially successful jetliners ever, with over "
            "5,000 delivered. It is the workhorse of low-cost carriers worldwide."
        ),
    },
    "Boeing 737-900 (B739)": {
        "manufacturer": "Boeing",
        "family": "737 Next Generation",
        "type": "Narrow-body",
        "engines": "2× CFM56-7B",
        "range_km": 5083,
        "capacity": "177–215",
        "wingspan_m": 35.8,
        "length_m": 42.1,
        "max_speed_kmh": 842,
        "first_flight": "2000",
        "intro": (
            "The longest 737 NG variant, the -900 was primarily ordered by Alaska Airlines and "
            "Indonesian carriers. The -900ER added exit doors for higher capacity."
        ),
    },
    "Boeing 767-300 (B763)": {
        "manufacturer": "Boeing",
        "family": "767",
        "type": "Wide-body",
        "engines": "2× GE CF6 or PW4000 or RR RB211",
        "range_km": 9700,
        "capacity": "218–269",
        "wingspan_m": 47.6,
        "length_m": 54.9,
        "max_speed_kmh": 913,
        "first_flight": "1986",
        "intro": (
            "The 767-300 extended the original 767-200 fuselage by 6.4 m. It was the dominant "
            "transatlantic widebody through the 1990s and is still widely used for cargo and charters."
        ),
    },
    "Boeing 777-300ER (B77W)": {
        "manufacturer": "Boeing",
        "family": "777",
        "type": "Wide-body",
        "engines": "2× GE90-115B",
        "range_km": 13650,
        "capacity": "350–550",
        "wingspan_m": 64.8,
        "length_m": 73.9,
        "max_speed_kmh": 905,
        "first_flight": "2003",
        "intro": (
            "The 777-300ER is powered by the world's most powerful commercial jet engines. "
            "It became the dominant long-haul widebody for premium carriers until the 787 and A350 arrived."
        ),
    },
    "Boeing 787-9 (B789)": {
        "manufacturer": "Boeing",
        "family": "787 Dreamliner",
        "type": "Wide-body",
        "engines": "2× GE GEnx or RR Trent 1000",
        "range_km": 14140,
        "capacity": "240–296",
        "wingspan_m": 60.1,
        "length_m": 62.8,
        "max_speed_kmh": 945,
        "first_flight": "2013",
        "intro": (
            "The 787-9 is the stretched Dreamliner, offering 20% better fuel efficiency than "
            "same-size predecessors. Its composite fuselage enables higher cabin humidity and pressure "
            "for improved passenger comfort on long-haul routes."
        ),
    },
    "Embraer ERJ-170 (E170)": {
        "manufacturer": "Embraer",
        "family": "E-Jet",
        "type": "Regional jet",
        "engines": "2× GE CF34-8E",
        "range_km": 3735,
        "capacity": "70–80",
        "wingspan_m": 26.0,
        "length_m": 29.9,
        "max_speed_kmh": 870,
        "first_flight": "2002",
        "intro": (
            "The E170 launched Embraer's E-Jet family, bringing mainline comfort (2-2 seating, "
            "no middle seats) to regional routes. It competes with the Bombardier CRJ-700."
        ),
    },
    "Embraer ERJ-190 (E190)": {
        "manufacturer": "Embraer",
        "family": "E-Jet",
        "type": "Regional jet",
        "engines": "2× GE CF34-10E",
        "range_km": 4537,
        "capacity": "96–114",
        "wingspan_m": 28.7,
        "length_m": 36.2,
        "max_speed_kmh": 870,
        "first_flight": "2004",
        "intro": (
            "The E190 is the most popular E-Jet variant. Its 2-2 seat layout means no passenger "
            "ever sits in a middle seat, making it a favourite for business travellers on short routes."
        ),
    },
}


@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    engine = create_engine(os.environ["NEON_DATABASE_URL"])
    df = pd.read_sql(
        "SELECT date, from_airport, to_airport, airline, aircraft, duration FROM flight_diary",
        engine,
    )
    df["duration_hrs"] = df["duration"].apply(
        lambda x: round(x.total_seconds() / 3600, 2) if x is not None else None
    )
    df["aircraft"] = df["aircraft"].str.strip().replace("()", None)
    return df


df = load_data()
known = sorted(df["aircraft"].dropna().unique())

sel = st.selectbox("Select an aircraft", known)
if not sel:
    st.stop()

specs = AIRCRAFT_SPECS.get(sel)
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
airline_counts = (
    flights_on_type["airline"].value_counts().reset_index()
)
airline_counts.columns = ["Airline", "Flights"]
st.dataframe(airline_counts, hide_index=True, width="stretch")

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
st.dataframe(routes[["Route", "Flights"]], hide_index=True, width="stretch")
