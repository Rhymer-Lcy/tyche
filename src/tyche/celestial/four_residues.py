"""四余 (罗睺/计都/月孛) — Meeus mean-element formulas, pure trigonometry, zero-dep.

- 罗睺 = the Moon's orbital ascending node (mean 黄白 node); 计都 = the descending node (罗睺 + 180°).
  (Follows the Indian -> 七政四余 mainstream: 罗睺 = ascending node, 计都 = descending node. Some
   schools swap them — a school convention — so this layer fixes ascending/descending and labels it,
   to be flipped in the 命理 layer if needed.)
- 月孛 = the Moon's orbital apogee longitude (mean) = perigee longitude + 180°.
- 紫炁 = a fictitious point, period ~28 years with no agreed epoch -> not decided here (left to the
  命理 layer, see docs).

All are mean elements; the true-node / true-apogee libration (~±1.5°) is omitted, which is enough
for sign entry — switch to true elements later if needed. Time is shifted back to UT by tz_offset_hours.
"""

from datetime import datetime, timedelta

from ..calendar.true_solar_time import _julian_day, CHINA_UTC_OFFSET_HOURS
from .zodiac import zodiac_position


def _julian_century(dt: datetime, tz_offset_hours: float) -> float:
    return (_julian_day(dt - timedelta(hours=tz_offset_hours)) - 2451545.0) / 36525.0


def four_residues(
    dt: datetime, tz_offset_hours: float = CHINA_UTC_OFFSET_HOURS
) -> dict:
    """Return {罗睺, 计都, 月孛}, each with its ecliptic longitude + 十二宫 placement (zodiac_position)."""
    t = _julian_century(dt, tz_offset_hours)

    # Moon's mean ascending-node longitude Ω (Meeus)
    omega = (125.04452 - 1934.136261 * t + 0.0020708 * t * t + t ** 3 / 450000) % 360
    # Moon's mean longitude L′ and mean anomaly M′ -> perigee longitude ϖ = L′ − M′; 月孛 = apogee = ϖ + 180
    lp = (218.3164477 + 481267.88123421 * t - 0.0015786 * t * t
          + t ** 3 / 538841 - t ** 4 / 65194000) % 360
    mp = (134.9633964 + 477198.8675055 * t + 0.0087414 * t * t
          + t ** 3 / 69699 - t ** 4 / 14712000) % 360
    yuebo = (lp - mp + 180) % 360

    return {
        "罗睺": zodiac_position(omega),
        "计都": zodiac_position((omega + 180) % 360),
        "月孛": zodiac_position(yuebo),
    }
