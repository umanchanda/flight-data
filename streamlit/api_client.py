import os

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv()


def _get_api_url() -> str:
    api_url = os.getenv("FLIGHT_API_URL")
    if not api_url:
        try:
            api_url = st.secrets.get("FLIGHT_API_URL")
        except StreamlitSecretNotFoundError:
            api_url = None
    if not api_url:
        raise RuntimeError(
            "FLIGHT_API_URL is not configured. Set it in Streamlit Cloud "
            "Secrets or in the local .env file."
        )
    return api_url.rstrip("/")


API_URL = _get_api_url()


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


@st.cache_data(ttl=60)
def load_aircraft() -> list[dict]:
    response = httpx.get(f"{API_URL}/aircraft", timeout=15)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600)
def load_registration(registration: str) -> dict:
    response = httpx.get(
        f"{API_URL}/registrations/{registration}",
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
