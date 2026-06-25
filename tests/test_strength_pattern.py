"""旺衰 scoring + month-command 取格 — golden-chart assertions + hand-crafted verification."""

from datetime import datetime

from tyche import build_chart, ChartConfig, chart_strength, chart_pattern
from tyche.chart.pillars import Chart, Pillar
from tyche.elements import ZHI_HIDDEN_GAN


def _mk(year, month, day, hour, **cfg) -> Chart:
    """Build a minimal Chart from four 干支 strings (for 旺衰/格局 only); **cfg goes to ChartConfig."""
    def P(gz):
        return Pillar(gz[0], gz[1], "", list(ZHI_HIDDEN_GAN[gz[1]]))
    dt = datetime(2000, 1, 1)
    # field order: ... hour, minggong, shengong, taiyuan, raw_eightchar
    return Chart(ChartConfig(**cfg), dt, dt, P(year), P(month), P(day), P(hour), "", "", "", None)


def test_chart1_strength_pattern():
    c = build_chart(datetime(1990, 6, 15, 14, 30), ChartConfig(gender="male", longitude=116.40))
    s = chart_strength(c)
    assert s["day_master"] == "辛"
    assert s["month_stage"] == "病"
    assert s["support"] == 2.5
    assert s["drain"] == 9.5
    assert s["level"] == "弱"
    p = chart_pattern(c)
    assert p["pattern"] == "七杀格"
    assert p["ge_gan"] == "丁"


def test_chart2_strength_pattern():
    c = build_chart(datetime(1985, 12, 20, 23, 40), ChartConfig(gender="female", longitude=121.47))
    s = chart_strength(c)
    assert s["day_master"] == "癸"
    assert s["month_stage"] == "临官"
    assert s["ratio"] == 0.5
    assert s["level"] == "中和"
    p = chart_pattern(c)
    assert p["pattern"] == "建禄格"


def test_pattern_special_cases():
    # month branch = DM's 临官 -> 建禄
    assert _pat(_mk("甲子", "丙寅", "甲午", "乙亥")) == "建禄格"   # 甲 at 寅 = 临官
    # month branch = DM's 帝旺 -> 月刃
    assert _pat(_mk("甲子", "丁卯", "甲午", "乙亥")) == "月刃格"   # 甲 at 卯 = 帝旺


def test_pattern_transmitted():
    # DM 甲, month 酉 (本气 辛 = 正官), year stem exposes 辛 -> 正官格
    ch = _mk("辛丑", "丁酉", "甲子", "乙亥")
    p = chart_pattern(ch)
    assert p["pattern"] == "正官格"
    assert p["ge_gan"] == "辛"
    assert "辛" in p["transmitted"]


def test_bijie_not_a_pattern_regression():
    """Regression: 壬 day in 申 month (申 hides 庚 偏印 / 壬 比劫 / 戊 七杀); the old impl mislabeled
    it 比肩格. 比劫 form no pattern -> 子平真诠 (default) takes the exposed 七杀 -> 七杀格
    (regression sample 壬午戊申壬申戊申)."""
    p = chart_pattern(_mk("壬午", "戊申", "壬申", "戊申"))
    assert p["pattern"] != "比肩格"          # bug does not recur
    assert p["pattern"] == "七杀格"
    assert p["ge_gan"] == "戊"


def test_pattern_school_switch():
    """古法当令 school: the in-command 偏印 本气 (unexposed) wins -> 偏印格, with 七杀 as 兼."""
    p = chart_pattern(_mk("壬午", "戊申", "壬申", "戊申", pattern_school="gufa_dangling"))
    assert p["pattern"] == "偏印格"
    assert "戊" in p["jian_shen"]            # the exposed 七杀 becomes a 兼神


def test_strength_levels_sane():
    # all 木/水 supporting 甲 木 -> 偏强/强
    strong = chart_strength(_mk("甲寅", "乙卯", "甲寅", "癸亥"))["level"]
    assert strong in ("强", "偏强")
    # all 金/火/土 draining 甲 木 -> 偏弱/弱
    weak = chart_strength(_mk("庚申", "辛酉", "甲戌", "戊辰"))["level"]
    assert weak in ("弱", "偏弱")


def _pat(ch):
    return chart_pattern(ch)["pattern"]
