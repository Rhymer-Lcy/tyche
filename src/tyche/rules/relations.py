"""地支 六合/六冲/三合/三会/六害/六破/三刑/自刑 + 天干 五合/相冲 detection.

Detected pairwise across a chart's four pillars; each hit records which pillars are involved.
PILLAR_ORDER is fixed 年→月→日→时 for stable output and tests.
"""

from itertools import combinations

PILLAR_ORDER = ["year", "month", "day", "hour"]

# ---------- 天干 (stems) ----------
# 五合 (combine-transform): 甲己→土, 乙庚→金, 丙辛→水, 丁壬→木, 戊癸→火
GAN_WUHE = {
    frozenset(["甲", "己"]): "土",
    frozenset(["乙", "庚"]): "金",
    frozenset(["丙", "辛"]): "水",
    frozenset(["丁", "壬"]): "木",
    frozenset(["戊", "癸"]): "火",
}
# 天干 four clashes (control + directional opposition): 甲庚, 乙辛, 丙壬, 丁癸 (戊己 土 sit centre, no clash)
GAN_CHONG = {frozenset(["甲", "庚"]), frozenset(["乙", "辛"]), frozenset(["丙", "壬"]), frozenset(["丁", "癸"])}

# ---------- 地支 (branches) ----------
# 六合 (combine-transform): 子丑→土, 寅亥→木, 卯戌→火, 辰酉→金, 巳申→水, 午未 (sun-moon, 火土)
ZHI_LIUHE = {
    frozenset(["子", "丑"]): "土",
    frozenset(["寅", "亥"]): "木",
    frozenset(["卯", "戌"]): "火",
    frozenset(["辰", "酉"]): "金",
    frozenset(["巳", "申"]): "水",
    frozenset(["午", "未"]): "火土",
}
# 六冲 (clash)
ZHI_CHONG = {
    frozenset(["子", "午"]), frozenset(["丑", "未"]), frozenset(["寅", "申"]),
    frozenset(["卯", "酉"]), frozenset(["辰", "戌"]), frozenset(["巳", "亥"]),
}
# 六害 (harm)
ZHI_HAI = {
    frozenset(["子", "未"]), frozenset(["丑", "午"]), frozenset(["寅", "巳"]),
    frozenset(["卯", "辰"]), frozenset(["申", "亥"]), frozenset(["酉", "戌"]),
}
# 六破 (break)
ZHI_PO = {
    frozenset(["子", "酉"]), frozenset(["午", "卯"]), frozenset(["申", "巳"]),
    frozenset(["寅", "亥"]), frozenset(["辰", "丑"]), frozenset(["戌", "未"]),
}
# 三合 bureaus (长生·帝旺·墓); the centre god = 帝旺 (index 1)
SANHE = {"水": ["申", "子", "辰"], "火": ["寅", "午", "戌"], "金": ["巳", "酉", "丑"], "木": ["亥", "卯", "未"]}
# 三会 directional bureaus
SANHUI = {"木": ["寅", "卯", "辰"], "火": ["巳", "午", "未"], "金": ["申", "酉", "戌"], "水": ["亥", "子", "丑"]}
# 三刑: 无恩 (寅巳申), 恃势 (丑戌未); 无礼 mutual (子卯); 自刑 self (辰午酉亥)
XING_TRIADS = {"无恩之刑": ["寅", "巳", "申"], "恃势之刑": ["丑", "戌", "未"]}
XING_ZIMAO = frozenset(["子", "卯"])  # 无礼之刑
XING_SELF = {"辰", "午", "酉", "亥"}   # 自刑 (same branch appearing twice)


def _present_pillars(branches: dict, targets: set) -> list[str]:
    """Return pillar names whose 地支 falls in targets, in fixed pillar order."""
    return [n for n in PILLAR_ORDER if n in branches and branches[n] in targets]


def _pairs(mapping: dict):
    """Enumerate all pillar pairs (in pillar order)."""
    names = [n for n in PILLAR_ORDER if n in mapping]
    return combinations(names, 2)


def detect_stem_relations(stems: dict) -> list[dict]:
    out = []
    for a, b in _pairs(stems):
        pair = frozenset([stems[a], stems[b]])
        if len(pair) == 2 and pair in GAN_WUHE:
            out.append({"type": "天干五合", "pillars": [a, b],
                        "items": [stems[a], stems[b]], "note": f"合化{GAN_WUHE[pair]}"})
        if len(pair) == 2 and pair in GAN_CHONG:
            out.append({"type": "天干相冲", "pillars": [a, b], "items": [stems[a], stems[b]]})
    return out


def detect_branch_relations(branches: dict) -> list[dict]:
    out = []

    # pairwise: 合 / 冲 / 害 / 破
    for a, b in _pairs(branches):
        za, zb = branches[a], branches[b]
        pair = frozenset([za, zb])
        if len(pair) == 2:
            if pair in ZHI_LIUHE:
                out.append({"type": "地支六合", "pillars": [a, b], "items": [za, zb],
                            "note": f"合化{ZHI_LIUHE[pair]}"})
            if pair in ZHI_CHONG:
                out.append({"type": "地支六冲", "pillars": [a, b], "items": [za, zb]})
            if pair in ZHI_HAI:
                out.append({"type": "地支六害", "pillars": [a, b], "items": [za, zb]})
            if pair in ZHI_PO:
                out.append({"type": "地支六破", "pillars": [a, b], "items": [za, zb]})

    # 三合 bureau / 半合 (two branches including the centre god)
    for elem, triad in SANHE.items():
        present = _present_pillars(branches, set(triad))
        zhis = [branches[n] for n in present]
        uniq = set(zhis)
        if uniq >= set(triad):
            out.append({"type": "三合局", "pillars": present, "items": triad, "note": f"{elem}局"})
        elif len(uniq) == 2 and triad[1] in uniq:  # centre god present -> 半合
            out.append({"type": "半合", "pillars": present, "items": sorted(uniq, key=triad.index),
                        "note": f"{elem}(半合)"})

    # 三会 (full)
    for elem, triad in SANHUI.items():
        present = _present_pillars(branches, set(triad))
        if set(branches[n] for n in present) >= set(triad):
            out.append({"type": "三会方", "pillars": present, "items": triad, "note": f"{elem}方"})

    # 三刑: all three -> 三刑; only two -> mutual 刑
    for name, triad in XING_TRIADS.items():
        present = _present_pillars(branches, set(triad))
        uniq = set(branches[n] for n in present)
        if uniq >= set(triad):
            out.append({"type": "三刑", "pillars": present, "items": triad, "note": name})
        elif len(uniq) == 2:
            out.append({"type": "相刑", "pillars": present, "items": sorted(uniq, key=triad.index),
                        "note": name})

    # 子卯 无礼之刑
    for a, b in _pairs(branches):
        if frozenset([branches[a], branches[b]]) == XING_ZIMAO:
            out.append({"type": "相刑", "pillars": [a, b], "items": [branches[a], branches[b]],
                        "note": "无礼之刑(子卯)"})

    # 自刑: same branch in 2+ pillars
    for z in XING_SELF:
        present = _present_pillars(branches, {z})
        if len(present) >= 2:
            out.append({"type": "自刑", "pillars": present, "items": [z] * len(present)})

    return out
