"""cast() orchestration + ChartReport + reading prompt."""

from datetime import datetime

from tyche import cast, ChartConfig, build_reading_prompt


def _report():
    return cast(datetime(1990, 6, 15, 14, 30),
                ChartConfig(gender="male", longitude=116.40))


def test_cast_structure():
    r = _report()
    # both the four pillars and the rule layer are on the report
    assert r.chart.year.ganzhi == "庚午"
    assert r.strength["level"] == "弱"
    assert r.pattern["pattern"] == "七杀格"   # 辛 金 day; 午 month 本气 丁 七杀, none exposed -> 七杀格
    assert r.relations and r.shensha           # non-empty
    assert r.reference_gan == "辛"


def test_to_dict_keys():
    d = _report().to_dict()
    for k in ("config", "solar_input", "solar_effective", "pillars",
              "minggong", "shengong", "taiyuan", "strength", "pattern",
              "relations", "shensha", "luck"):
        assert k in d, k
    assert d["shengong"] == "戊寅"
    assert d["luck"]["is_forward"] is True and "xiao_yun" in d["luck"]
    assert set(d["pillars"]) == {"year", "month", "day", "hour"}
    assert d["pillars"]["day"]["ganzhi"] == "辛亥"
    assert "ten_gods" in d["pillars"]["day"]


def test_reading_prompt():
    p = build_reading_prompt(_report(), "事业财运")
    assert set(p) == {"system", "user"}
    assert "勿重算" not in p["user"]            # the constraint lives in system, not user
    assert "勿重算" in p["system"] or "不要重新排盘" in p["system"]
    assert "庚午" in p["user"] and "七杀格" in p["user"] and "事业财运" in p["user"]
