from typing import Optional
import httpx

ADSBDB_URL = "https://api.adsbdb.com/v0/aircraft/{reg}"


def _photo_url_valid(url: str) -> bool:
    try:
        r = httpx.head(url, timeout=4, follow_redirects=True)
        return r.status_code == 200 and "image" in r.headers.get("content-type", "")
    except httpx.RequestError:
        return False


def fetch_registration(reg: str) -> Optional[dict]:
    """Return aircraft metadata from adsbdb.com, or None if not found."""
    try:
        r = httpx.get(ADSBDB_URL.format(reg=reg.upper()), timeout=6)
        if r.status_code == 200:
            aircraft = r.json().get("response", {}).get("aircraft")
            if isinstance(aircraft, dict):
                url = aircraft.get("url_photo")
                if url and not _photo_url_valid(url):
                    aircraft["url_photo"] = None
            return aircraft
    except httpx.RequestError:
        pass
    return None
