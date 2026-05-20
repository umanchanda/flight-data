from typing import Optional
import httpx

ADSBDB_URL = "https://api.adsbdb.com/v0/aircraft/{reg}"
OPENSKY_URL = "https://opensky-network.org/api/metadata/aircraft/icao/{icao}"
PLANESPOTTERS_URL = "https://api.planespotters.net/pub/photos/reg/{reg}"
PLANESPOTTERS_UA = "fr24-personal-app/1.0 (+mailto:uday.manchanda14@gmail.com)"


def fetch_photo(reg: str) -> Optional[dict]:
    """Return photo info from Planespotters.net: {url, photographer, link}."""
    try:
        r = httpx.get(
            PLANESPOTTERS_URL.format(reg=reg.upper()),
            headers={"User-Agent": PLANESPOTTERS_UA},
            timeout=6,
        )
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                p = photos[0]
                return {
                    "url": p.get("thumbnail_large", {}).get("src"),
                    "photographer": p.get("photographer"),
                    "link": p.get("link"),
                }
    except httpx.RequestError:
        pass
    return None


def _fetch_year_built(icao_hex: str) -> Optional[str]:
    """Return the year the aircraft was built from OpenSky, or None."""
    try:
        r = httpx.get(OPENSKY_URL.format(icao=icao_hex.upper()), timeout=6)
        if r.status_code == 200:
            built = r.json().get("built")
            if built:
                return str(built)[:4]  # "2008-01-01" → "2008"
    except httpx.RequestError:
        pass
    return None


def fetch_registration(reg: str) -> Optional[dict]:
    """Return aircraft metadata from adsbdb.com (augmented with year built), or None."""
    try:
        r = httpx.get(ADSBDB_URL.format(reg=reg.upper()), timeout=6)
        if r.status_code == 200:
            aircraft = r.json().get("response", {}).get("aircraft")
            if isinstance(aircraft, dict):
                icao_hex = aircraft.get("mode_s")
                if icao_hex:
                    aircraft["year_built"] = _fetch_year_built(icao_hex)
                return aircraft
    except httpx.RequestError:
        pass
    return None
