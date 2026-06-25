"""True solar time correction.

The 时柱 is fixed by true (apparent) solar time, not clock time. Two corrections:
  1. Longitude offset = (birth longitude − standard meridian) × 4 min/degree.
     China uses UTC+8 (120°E), so places to the east run ahead of the clock.
  2. Equation of time (EoT) — the apparent sun's fast/slow caused by orbital
     eccentricity and obliquity, ranging about −14.2 (Feb 11) to +16.5 (Nov 3) min over a year.

true solar time = clock time + longitude offset + EoT (EoT as apparent − mean; positive = sundial fast)

Accuracy: EoT uses the Meeus (Astronomical Algorithms) closed form, the same as the NOAA
Solar Calculator: about ±0.01 min over 1900–2100, checked against authoritative tables (see tests).
Pure trigonometry, zero dependencies. (An earlier Spencer/PV approximation peaked at ~1.5 min
error — enough to flip a chart at a day/year boundary — and was dropped.)
"""

import math
from datetime import datetime, timedelta

CHINA_STANDARD_MERIDIAN = 120.0  # standard meridian of UTC+8
CHINA_UTC_OFFSET_HOURS = 8.0


def _julian_day(dt: datetime) -> float:
    """Gregorian datetime (treated as UT) -> Julian Day."""
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def equation_of_time_minutes(
    dt: datetime, utc_offset_hours: float = CHINA_UTC_OFFSET_HOURS
) -> float:
    """Equation of time in minutes; positive means true (apparent) solar time runs ahead of mean.

    Meeus closed form. dt is local clock time, shifted back to UT by utc_offset_hours for the
    sun's position (the intraday EoT change is < 0.02 min, negligible, but applied for rigor).
    """
    t = (_julian_day(dt - timedelta(hours=utc_offset_hours)) - 2451545.0) / 36525.0
    # sun's geometric mean longitude L0, mean anomaly M, orbital eccentricity e (deg / deg / unitless)
    l0 = math.radians((280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360)
    m = math.radians(357.52911 + t * (35999.05029 - 0.0001537 * t))
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    # obliquity ε (with the leading nutation term) -> y = tan^2(ε/2)
    eps0 = 23 + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60
    eps = math.radians(eps0 + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * t)))
    y = math.tan(eps / 2) ** 2
    e_rad = (
        y * math.sin(2 * l0)
        - 2 * e * math.sin(m)
        + 4 * e * y * math.sin(m) * math.cos(2 * l0)
        - 0.5 * y * y * math.sin(4 * l0)
        - 1.25 * e * e * math.sin(2 * m)
    )
    return 4 * math.degrees(e_rad)


def longitude_correction_minutes(
    longitude: float, standard_meridian: float = CHINA_STANDARD_MERIDIAN
) -> float:
    """Longitude offset in minutes. East longitude is positive."""
    return (longitude - standard_meridian) * 4.0


def apply_true_solar_time(
    dt: datetime,
    longitude: float,
    standard_meridian: float = CHINA_STANDARD_MERIDIAN,
) -> datetime:
    """Correct clock time to true solar time."""
    eot = equation_of_time_minutes(dt, utc_offset_hours=standard_meridian / 15.0)
    offset = longitude_correction_minutes(longitude, standard_meridian) + eot
    return dt + timedelta(minutes=offset)
