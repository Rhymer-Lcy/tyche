"""七政四余 astronomy layer.

四余 + 黄道十二宫: pure formula, always runs.
七政: needs skyfield + a local ephemeris (runtime/eph/de421.bsp); skipped if absent
(CI has no ephemeris, so 七政 is not exercised there).
"""

from datetime import datetime
from pathlib import Path

import pytest

from tyche.celestial import four_residues, zodiac_position


# ───────── 黄道十二宫 (pure) ─────────
def test_zodiac_position():
    assert zodiac_position(0) == {"lon": 0.0, "sign": "白羊", "sign_index": 0,
                                  "degree": 0.0, "palace_branch": "戌"}
    p = zodiac_position(95.0)        # 巨蟹 (90-120)
    assert p["sign"] == "巨蟹" and p["sign_index"] == 3 and p["degree"] == 5.0
    assert p["palace_branch"] == "未"
    assert zodiac_position(360.0)["sign"] == "白羊"     # wrap-around
    assert zodiac_position(359.9)["sign"] == "双鱼"


# ───────── 四余 (Meeus mean-element, pure) ─────────
def test_four_residues_j2000():
    fr = four_residues(datetime(2000, 1, 1, 20, 0))   # J2000 = 12:00 UTC
    assert abs(fr["罗睺"]["lon"] - 125.045) < 0.01     # Meeus mean ascending node
    assert abs(fr["月孛"]["lon"] - 263.353) < 0.01     # L′ − M′ + 180
    # 计都 = 罗睺 + 180
    assert abs((fr["罗睺"]["lon"] + 180) % 360 - fr["计都"]["lon"]) < 1e-6
    assert fr["罗睺"]["sign"] == "狮子" and fr["罗睺"]["palace_branch"] == "午"


def test_four_residues_node_retrograde():
    # the 黄白 node moves backward: an earlier instant has a larger longitude
    early = four_residues(datetime(1990, 6, 15, 14, 30))["罗睺"]["lon"]
    late = four_residues(datetime(2000, 1, 1, 20, 0))["罗睺"]["lon"]
    assert early > late


# ───────── 七政 (skyfield + ephemeris; skipped if absent) ─────────
_EPH = Path(__file__).resolve().parent.parent / "runtime" / "eph"
try:
    import skyfield  # noqa: F401
    _READY = (_EPH / "de421.bsp").exists()
except ImportError:
    _READY = False

_skip = pytest.mark.skipif(not _READY, reason="needs skyfield + a local de421.bsp (runtime/eph)")


@_skip
def test_seven_governors_equinox():
    from tyche.celestial.seven_governors import seven_governors
    # 2000 vernal equinox 07:35 UTC = 15:35 CST -> sun's ecliptic longitude ≈ 0°
    sg = seven_governors(datetime(2000, 3, 20, 15, 35), ephemeris=str(_EPH))
    lon = sg["日"]["lon"]
    assert min(lon, 360 - lon) < 0.5


@_skip
def test_seven_governors_signs_and_retrograde():
    from tyche.celestial.seven_governors import seven_governors
    sg = seven_governors(datetime(1990, 6, 15, 14, 30), ephemeris=str(_EPH))
    assert sg["日"]["sign"] == "双子" and sg["日"]["palace_branch"] == "申"
    assert sg["土"]["retrograde"] is True       # Saturn was retrograde in 1990-06
    assert "retrograde" in sg["水"]             # planets carry a retrograde flag
    assert "retrograde" not in sg["日"] and "retrograde" not in sg["月"]
