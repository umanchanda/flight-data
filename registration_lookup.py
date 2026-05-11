from typing import Optional
import httpx

ADSBDB_URL = "https://api.adsbdb.com/v0/aircraft/{reg}"


def fetch_registration(reg: str) -> Optional[dict]:
    """Return aircraft metadata from adsbdb.com, or None if not found."""
    try:
        r = httpx.get(ADSBDB_URL.format(reg=reg.upper()), timeout=6)
        if r.status_code == 200:
            return r.json().get("response", {}).get("aircraft")
    except httpx.RequestError:
        pass
    return None
