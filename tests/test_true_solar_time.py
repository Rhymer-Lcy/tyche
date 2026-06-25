"""True solar time: longitude offset + equation of time (Meeus, checked against authoritative
tables) + charting-boundary integration."""

from datetime import datetime

from tyche import ChartConfig
from tyche.chart.pillars import build_chart
from tyche.calendar.true_solar_time import (
    apply_true_solar_time,
    equation_of_time_minutes,
    longitude_correction_minutes,
)


def test_longitude_correction():
    # 116.40E vs 120E: (116.40 - 120) * 4 = -14.4 min
    assert abs(longitude_correction_minutes(116.40) - (-14.4)) < 1e-9
    assert longitude_correction_minutes(120.0) == 0.0       # the standard meridian has no offset
    assert longitude_correction_minutes(124.0) == 16.0      # east is positive, true solar time runs fast


# Authoritative values (minutes, apparent - mean) from astronomical almanacs / NOAA; the two
# extremes and the four zeros.
_EOT_GOLDEN = {
    (2, 11): -14.24,   # annual minimum
    (5, 14): +3.66,
    (7, 26): -6.54,
    (11, 3): +16.48,   # annual maximum
    (4, 15): 0.0,      # zero
    (6, 13): 0.0,
    (9, 1): 0.0,
    (12, 25): 0.0,
}


def test_equation_of_time_authoritative():
    for (m, d), expected in _EOT_GOLDEN.items():
        eot = equation_of_time_minutes(datetime(2000, m, d, 12))
        assert abs(eot - expected) < 0.35, f"{m}/{d}: {eot:.2f} vs {expected}"


def test_equation_of_time_bounded():
    for month in range(1, 13):
        eot = equation_of_time_minutes(datetime(2000, month, 15, 12))
        assert -15.0 < eot < 17.0


def test_apply_true_solar_time_beijing():
    dt = datetime(1990, 6, 15, 14, 30)
    eff = apply_true_solar_time(dt, 116.40)
    # mid-June EoT is tiny, the main correction is -14.4 min, landing in 14:14-14:16
    assert eff.hour == 14 and 14 <= eff.minute <= 16


def test_no_correction_when_longitude_none():
    dt = datetime(1990, 6, 15, 14, 30)
    chart = build_chart(dt, ChartConfig(longitude=None))
    assert chart.solar_effective == chart.solar_input == dt


def test_tst_crosses_midnight_changes_day_pillar():
    """A far-west longitude (75E) rolls 00:30 back to the previous day -> the 日柱/时柱 change."""
    dt = datetime(2000, 3, 10, 0, 30)
    off = build_chart(dt, ChartConfig(longitude=None))
    on = build_chart(dt, ChartConfig(longitude=75.0))
    assert (off.day.ganzhi, off.hour.ganzhi) == ("丁卯", "庚子")
    assert on.solar_effective.day == 9                  # rolled back to the previous day
    assert (on.day.ganzhi, on.hour.ganzhi) == ("丙寅", "己亥")


def test_tst_crosses_lichun_changes_year_pillar():
    """05:00 just after 立春 (2001-02-04 02:28); 75E pulls it back before 立春 -> 年/月柱 change, 日柱 unchanged."""
    dt = datetime(2001, 2, 4, 5, 0)
    off = build_chart(dt, ChartConfig(longitude=None))
    on = build_chart(dt, ChartConfig(longitude=75.0))
    assert (off.year.ganzhi, off.month.ganzhi) == ("辛巳", "庚寅")
    assert (on.year.ganzhi, on.month.ganzhi) == ("庚辰", "己丑")
    assert off.day.ganzhi == on.day.ganzhi == "戊戌"     # no midnight crossing, 日柱 unchanged


def test_eastward_longitude_speeds_up():
    # east of 120: true solar time runs ahead of the clock (positive offset)
    dt = datetime(2000, 6, 13, 12, 0)   # a day with EoT ≈ 0, to isolate the longitude term
    eff = apply_true_solar_time(dt, 135.0)
    assert eff > dt and abs((eff - dt).total_seconds() / 60 - 60.0) < 1.0
