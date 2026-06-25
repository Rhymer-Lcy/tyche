"""神煞 — 空亡 algorithm + golden-chart assertions + 太极点-switch verification."""

from datetime import datetime

from tyche import build_chart, ChartConfig
from tyche.rules import detect_shensha
from tyche.rules.shensha import xunkong_branches


def _ss(dt, ref="day", **kw):
    c = build_chart(dt, ChartConfig(reference_pillar=ref, **kw))
    return {s["name"]: list(zip(s["hit_pillars"], s["hit_branches"])) for s in detect_shensha(c)}


def test_xunkong():
    assert set(xunkong_branches("甲子")) == {"戌", "亥"}   # 甲子 旬
    assert set(xunkong_branches("辛亥")) == {"寅", "卯"}   # 甲辰 旬
    assert set(xunkong_branches("庚午")) == {"戌", "亥"}   # 甲子 旬
    assert set(xunkong_branches("癸巳")) == {"午", "未"}   # 甲申 旬


def test_chart1_shensha_day_taiji():
    s = _ss(datetime(1990, 6, 15, 14, 30), "day", gender="male", longitude=116.40)
    assert s["天乙贵人"] == [("year", "午"), ("month", "午")]
    assert s["华盖"] == [("hour", "未")]
    assert "将星" not in s


def test_chart1_shensha_year_taiji_switch():
    """Same chart, 太极点 switched to year: 神煞 change wholesale — the core differentiator verified."""
    s = _ss(datetime(1990, 6, 15, 14, 30), "year", gender="male", longitude=116.40)
    assert s["天乙贵人"] == [("hour", "未")]      # anchor moves from day stem 辛 -> year stem 庚
    assert s["文昌贵人"] == [("day", "亥")]
    assert s["将星"] == [("year", "午"), ("month", "午")]
    assert s["空亡"] == [("day", "亥")]            # 旬空 moves from the day-pillar 旬 -> year-pillar 旬


def test_chart2_shensha_day_taiji():
    s = _ss(datetime(1985, 12, 20, 23, 40), "day", gender="female", longitude=121.47)
    assert s["天乙贵人"] == [("day", "巳")]
    assert s["禄神"] == [("month", "子"), ("hour", "子")]
    assert s["华盖"] == [("year", "丑")]


def test_guchen_guasu_always_year():
    """孤辰/寡宿 always anchor on the year branch, not the 太极点 — day/year should match."""
    dt = datetime(1990, 6, 15, 14, 30)
    day = {s["name"]: s["anchor_value"] for s in detect_shensha(
        build_chart(dt, ChartConfig(reference_pillar="day", longitude=116.40)))}
    year = {s["name"]: s["anchor_value"] for s in detect_shensha(
        build_chart(dt, ChartConfig(reference_pillar="year", longitude=116.40)))}
    # if present, 孤辰/寡宿 anchor on the year branch (午) regardless of the 太极点
    for name in ("孤辰", "寡宿"):
        if name in day:
            assert day[name] == "午"
        if name in year:
            assert year[name] == "午"
