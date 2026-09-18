import os

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FLIGHT_API_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=60)
def load_flights() -> pd.DataFrame:
    rows = []
    limit = 1000
    offset = 0

    while True:
        response = httpx.get(
            f"{API_URL}/flights",
            params={"limit": limit, "offset": offset},
            timeout=15,
        )
        response.raise_for_status()
        batch = response.json()
        rows.extend(batch)

        if len(batch) < limit:
            break
        offset += limit

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["aircraft"] = df["aircraft"].str.strip().replace("()", None)
    df["duration_hrs"] = (df["duration_minutes"] / 60).round(2)
    return df.drop(columns=["duration_minutes"])


@st.cache_data(ttl=3600)
def load_registration(registration: str) -> dict:
    response = httpx.get(
        f"{API_URL}/registrations/{registration}",
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
