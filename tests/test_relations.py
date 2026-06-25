"""刑冲合害会破 — golden-chart assertions + hand-crafted unit cases."""

from datetime import datetime

from tyche import build_chart, ChartConfig, analyze
from tyche.rules.relations import detect_branch_relations, detect_stem_relations


def _rels(dt, **kw):
    return analyze(build_chart(dt, ChartConfig(**kw)))["relations"]


def _has(rl, type_, pillars=None, note=None):
    for r in rl:
        if r["type"] != type_:
            continue
        if pillars is not None and set(r["pillars"]) != set(pillars):
            continue
        if note is not None and r.get("note") != note:
            continue
        return True
    return False


def test_chart1_relations():
    rl = _rels(datetime(1990, 6, 15, 14, 30), gender="male", longitude=116.40)
    assert _has(rl, "天干五合", ["year", "hour"], "合化金")     # 庚 + 乙
    assert _has(rl, "天干相冲", ["day", "hour"])                # 辛 + 乙
    assert _has(rl, "地支六合", ["year", "hour"], "合化火土")   # 午 + 未
    assert _has(rl, "地支六合", ["month", "hour"], "合化火土")
    assert _has(rl, "自刑", ["year", "month"])                 # 午 + 午


def test_chart2_relations():
    rl = _rels(datetime(1985, 12, 20, 23, 40), gender="female", longitude=121.47)
    assert _has(rl, "天干五合", ["month", "day"], "合化火")     # 戊 + 癸
    assert _has(rl, "地支六合", ["year", "month"])             # 丑 + 子
    assert _has(rl, "地支六合", ["year", "hour"])
    assert not _has(rl, "自刑")  # 子 is not a 自刑 branch


def test_crafted_branch_relations():
    r = detect_branch_relations({"year": "申", "month": "子", "day": "辰", "hour": "寅"})
    assert any(x["type"] == "三合局" and x["note"] == "水局" for x in r)

    r = detect_branch_relations({"year": "子", "month": "午", "day": "卯", "hour": "酉"})
    assert any(x["type"] == "地支六冲" and set(x["items"]) == {"卯", "酉"} for x in r)
    assert any(x["type"] == "地支六冲" and set(x["items"]) == {"子", "午"} for x in r)

    r = detect_branch_relations({"year": "寅", "month": "巳", "day": "申", "hour": "子"})
    assert any(x["type"] == "三刑" and x["note"] == "无恩之刑" for x in r)

    # 申子 半合 (centre god 子 present)
    r = detect_branch_relations({"year": "申", "month": "子", "day": "寅", "hour": "卯"})
    assert any(x["type"] == "半合" for x in r)

    # 子卯 无礼之刑
    r = detect_branch_relations({"year": "子", "month": "卯", "day": "丑", "hour": "辰"})
    assert any(x["type"] == "相刑" and "子卯" in x["note"] for x in r)

    # 三会 木方 寅卯辰
    r = detect_branch_relations({"year": "寅", "month": "卯", "day": "辰", "hour": "子"})
    assert any(x["type"] == "三会方" and x["note"] == "木方" for x in r)


def test_crafted_stem_relations():
    r = detect_stem_relations({"year": "甲", "month": "己", "day": "丙", "hour": "戊"})
    assert any(x["type"] == "天干五合" and x["note"] == "合化土" for x in r)
    r = detect_stem_relations({"year": "丙", "month": "壬", "day": "甲", "hour": "乙"})
    assert any(x["type"] == "天干相冲" and set(x["items"]) == {"丙", "壬"} for x in r)
