"""
Shared timezone lookup — wraps TimezoneFinder with a sensible fallback.

get_timezone(lat, lon)  →  str  (e.g. "Australia/Adelaide")
"""

_tf = None


def _get_tf():
    global _tf
    if _tf is None:
        try:
            from timezonefinder import TimezoneFinder
            _tf = TimezoneFinder()
        except ImportError:
            pass
    return _tf


def get_timezone(lat: float, lon: float, fallback: str = "UTC") -> str:
    """Return the IANA timezone string for a lat/lon coordinate.

    Falls back to *fallback* (default "UTC") if TimezoneFinder is not
    installed or the coordinate is over international waters.
    """
    tf = _get_tf()
    if tf is None:
        return fallback
    tz = tf.timezone_at(lat=lat, lng=lon)
    return tz if tz else fallback
