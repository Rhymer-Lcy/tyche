"""七政 (sun/moon + 水金火木土) — geocentric apparent ecliptic longitude (of-date) + retrograde, via skyfield.

- Uses the geocentric apparent position (aberration/nutation included), longitude in the date's
  ecliptic (epoch=t), consistent with the 十二宫 layer. The Moon is geocentric (no topocentric
  parallax, ~±1°), matching the 命理 tradition.
- Retrograde: judged by the sign of the +1-day longitude delta (sun/moon never retrograde, always False).
- Time is shifted back to UT by tz_offset_hours (positions are the true instant, unrelated to true solar time).

Needs the optional skyfield dependency + an ephemeris kernel (see ephemeris).
"""

from datetime import datetime, timedelta

from ..calendar.true_solar_time import CHINA_UTC_OFFSET_HOURS
from .ephemeris import get_ephemeris
from .zodiac import zodiac_position

# (Chinese name, skyfield target, is_planet [judge retrograde])
_BODIES = [
    ("日", "sun", False),
    ("月", "moon", False),
    ("水", "mercury", True),
    ("金", "venus", True),
    ("火", "mars", True),
    ("木", "jupiter barycenter", True),
    ("土", "saturn barycenter", True),
]


def _signed_delta(a: float, b: float) -> float:
    """Signed longitude delta of b relative to a, in (-180, 180]."""
    return (b - a + 180) % 360 - 180


def seven_governors(
    dt: datetime,
    tz_offset_hours: float = CHINA_UTC_OFFSET_HOURS,
    ephemeris: str | None = None,
) -> dict:
    """Return {日,月,水,金,火,木,土}, each with longitude + 十二宫 placement + retrograde (planets)."""
    eph, ts = get_ephemeris(ephemeris)
    earth = eph["earth"]
    utc = dt - timedelta(hours=tz_offset_hours)
    t = ts.utc(utc.year, utc.month, utc.day, utc.hour, utc.minute, utc.second)
    t_next = ts.utc(utc.year, utc.month, utc.day + 1, utc.hour, utc.minute, utc.second)

    def lon_at(body, tt) -> float:
        _, lon, _ = earth.at(tt).observe(body).apparent().ecliptic_latlon(epoch=tt)
        return float(lon.degrees) % 360   # to native float (skyfield returns numpy)

    out = {}
    for name, key, is_planet in _BODIES:
        body = eph[key]
        lon = lon_at(body, t)
        pos = zodiac_position(lon)
        if is_planet:
            pos["retrograde"] = bool(_signed_delta(lon, lon_at(body, t_next)) < 0)
        out[name] = pos
    return out
