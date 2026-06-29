"""
Shared timezone lookup — wraps TimezoneFinder with a sensible fallback.

get_timezone(lat, lon)  →  str  (e.g. "Australia/Adelaide")
"""


def get_timezone(lat: float, lon: float, fallback: str = "UTC") -> str:
    """Return the IANA timezone string for a lat/lon coordinate.

    Falls back to *fallback* (default "UTC") if TimezoneFinder is not
    installed or the coordinate is over international waters.
    """
    try:
        from timezonefinder import TimezoneFinder
        tz = TimezoneFinder().timezone_at(lat=lat, lng=lon)
        return tz if tz else fallback
    except ImportError:
        return fallback
