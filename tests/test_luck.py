"""大运 direction / 童限 小运 / 流年 (干支 + 太极点 十神 + enclosing 大运/小运/旬空).

Chart: 1990-06-15 14:30 male, longitude 116.40 -> 庚午 壬午 辛亥 乙未 (辛 金 day; 庚午 yang year,
male -> forward). The asserted values were all hand-verified.
"""

from datetime import datetime

import pytest

from tyche import (
    ChartConfig, fleeting_year, fleeting_years, fleeting_months, luck_cycles,
)
from tyche.chart.luck import _months_by_wuhu
from tyche.chart.pillars import build_chart


def _chart(ref="day"):
    return build_chart(datetime(1990, 6, 15, 14, 30),
                       ChartConfig(gender="male", longitude=116.40, reference_pillar=ref))


def test_shengong():
    assert _chart().shengong == "戊寅"


def test_direction_and_dayun_range():
    luck = luck_cycles(_chart())
    assert luck["is_forward"] is True            # 庚午 yang year + male -> forward
    dy1 = luck["da_yun"][1]
    assert dy1["ganzhi"] == "癸未"               # stepped forward from the month pillar 壬午
    assert dy1["start_age"] == 8 and dy1["end_age"] == 17
    assert dy1["start_year"] == 1997 and dy1["end_year"] == 2006


def test_dayun_ten_gods():
    luck = luck_cycles(_chart())
    # pre-起运 stage (index 0): empty ganzhi, ten_gods None (the guard)
    assert luck["da_yun"][0]["ganzhi"] == "" and luck["da_yun"][0]["ten_gods"] is None
    # 大运 十神 follow the 太极点 (here 子平 = day stem 辛): 癸未 -> stem 食神
    tg = luck["da_yun"][1]["ten_gods"]
    assert tg["gan"] == "食神"                    # ten_god(辛, 癸)
    assert tg["hidden"] == {"己": "偏印", "丁": "七杀", "乙": "偏财"}


def test_dayun_ten_gods_taiji_switch():
    # 太极点 day->year: the 癸未 大运 stem 十神 goes 食神 (vs 辛) -> 伤官 (vs 庚)
    assert luck_cycles(_chart("day"))["da_yun"][1]["ten_gods"]["gan"] == "食神"
    assert luck_cycles(_chart("year"))["da_yun"][1]["ten_gods"]["gan"] == "伤官"


def test_childhood_xiao_yun():
    xy = luck_cycles(_chart())["xiao_yun"]
    assert len(xy) == 7                          # the 7 pre-起运 years (起运 at age 8)
    assert (xy[0]["year"], xy[0]["age"], xy[0]["ganzhi"]) == (1990, 1, "丙申")  # one step forward from 时柱 乙未
    assert (xy[-1]["year"], xy[-1]["age"], xy[-1]["ganzhi"]) == (1996, 7, "壬寅")
    # 小运 also carry 太极点 十神: 丙申 -> stem 正官
    assert xy[0]["ten_gods"]["gan"] == "正官"     # ten_god(辛, 丙)
    assert xy[0]["ten_gods"]["hidden"] == {"庚": "劫财", "壬": "伤官", "戊": "正印"}


def test_fleeting_year_full():
    fy = fleeting_year(_chart(), 1997)
    assert fy["ganzhi"] == "丁丑" and fy["age"] == 8
    assert fy["ten_gods"]["gan"] == "七杀"        # ten_god(辛, 丁)
    assert fy["ten_gods"]["hidden"] == {"己": "偏印", "癸": "食神", "辛": "比肩"}
    assert fy["dayun"] == "癸未"
    assert fy["xiao_yun"] == "癸卯"               # one step forward from 壬寅 (age 7)
    assert fy["xun_kong"] == "申酉"


def test_fleeting_year_taiji_switch():
    # same 流年, 太极点 day->year: the 流年 stem 十神 goes 七杀 (vs day stem 辛) -> 正官 (vs year stem 庚)
    assert fleeting_year(_chart("day"), 1997)["ten_gods"]["gan"] == "七杀"
    assert fleeting_year(_chart("year"), 1997)["ten_gods"]["gan"] == "正官"


def test_fleeting_year_2025():
    fy = fleeting_year(_chart(), 2025)
    assert fy["ganzhi"] == "乙巳" and fy["age"] == 36
    assert fy["ten_gods"]["gan"] == "偏财"        # ten_god(辛, 乙)
    assert fy["dayun"] == "乙酉"


def test_fleeting_year_out_of_range_fallback():
    fy = fleeting_year(_chart(), 2200)
    assert fy["ganzhi"] == "庚子"                 # taken directly from the 立春-based year 干支
    assert fy["dayun"] is None and fy["xiao_yun"] is None and fy["age"] is None


def test_fleeting_years_range():
    rng = fleeting_years(_chart(), 2024, 2026)
    assert [f["ganzhi"] for f in rng] == ["甲辰", "乙巳", "丙午"]
    with pytest.raises(ValueError):
        fleeting_years(_chart(), 2026, 2024)


def test_fleeting_months():
    fm = fleeting_months(_chart(), 2025)   # 乙巳 year: 五虎遁 "乙庚 戊 first" -> 正月 戊寅
    assert len(fm) == 12
    assert [m["ganzhi"] for m in fm] == [
        "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
        "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑",
    ]
    assert (fm[0]["index"], fm[0]["month"]) == (0, "正")
    assert fm[11]["month"] == "腊"
    # 太极点 十神 (子平 vs 辛): 正月 戊寅 -> stem 正印
    assert fm[0]["ten_gods"]["gan"] == "正印"
    assert fm[0]["ten_gods"]["hidden"] == {"甲": "正财", "丙": "正官", "戊": "正印"}
    assert fm[0]["xun_kong"] == "申酉"


def test_fleeting_months_wuhu_matches_kernel():
    # the 五虎遁 fallback sequence must match the core's LiuYue (2025 = 乙巳 year)
    kernel = [m["ganzhi"] for m in fleeting_months(_chart(), 2025)]
    assert kernel == _months_by_wuhu("乙")


def test_fleeting_months_out_of_range_fallback():
    fm = fleeting_months(_chart(), 2200)   # 庚子 year -> 五虎遁 正月 戊寅, 旬空 left empty
    assert fm[0]["ganzhi"] == "戊寅" and fm[0]["xun_kong"] is None
    assert len(fm) == 12
