from typing import Optional
import httpx

ADSBDB_URL = "https://api.adsbdb.com/v0/aircraft/{reg}"
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


def fetch_registration(reg: str) -> Optional[dict]:
    """Return aircraft metadata from adsbdb.com, or None if not found."""
    try:
        r = httpx.get(ADSBDB_URL.format(reg=reg.upper()), timeout=6)
        if r.status_code == 200:
            aircraft = r.json().get("response", {}).get("aircraft")
            if isinstance(aircraft, dict):
                return aircraft
    except httpx.RequestError:
        pass
    return None
