"""神煞 engine: reads data/shensha.yaml, routes the anchor by the 太极点, and finds hits
among the four pillars' 地支.

太极点 routing: 神煞 with reference="taiji" take their anchor stem/branch from the self pillar
(子平=day, 禄命星命=year), switching automatically with ChartConfig.reference_pillar;
reference="year"/"day" are fixed.
"""

import functools
from pathlib import Path

import yaml

from ..chart.pillars import Chart
from ..elements import GAN, ZHI

PILLAR_ORDER = ["year", "month", "day", "hour"]
_DATA = Path(__file__).parent / "data" / "shensha.yaml"


@functools.lru_cache(maxsize=1)
def _rules() -> dict:
    return yaml.safe_load(_DATA.read_text(encoding="utf-8"))


def xunkong_branches(ganzhi: str) -> list[str]:
    """Return the two 空亡 branches of the 旬 containing a 干支."""
    gi = GAN.index(ganzhi[0])
    zi = ZHI.index(ganzhi[1])
    # locate within the 60 甲子: n % 10 == gi and n % 12 == zi
    n = next(k for k in range(gi, 60, 10) if k % 12 == zi)
    head_zhi = (n // 10) * 10 % 12          # branch index of the 旬 head
    return [ZHI[(head_zhi + 10) % 12], ZHI[(head_zhi + 11) % 12]]


def _ref_pillar(chart: Chart, reference: str):
    if reference == "taiji":
        return chart.day if chart.config.reference_pillar == "day" else chart.year
    if reference == "year":
        return chart.year
    if reference == "day":
        return chart.day
    raise ValueError(f"unknown reference: {reference}")


def detect_shensha(chart: Chart) -> list[dict]:
    """Return matched 神煞: {name, anchor_value, hit_pillars, hit_branches, reference, desc}."""
    out = []
    branches = {n: p.zhi for n, p in chart.pillars.items()}

    for name, rule in _rules().items():
        ref_pillar = _ref_pillar(chart, rule["reference"])

        if rule.get("kind") == "xunkong":
            targets = set(xunkong_branches(ref_pillar.ganzhi))
            anchor_value = ref_pillar.ganzhi
        else:
            anchor_value = ref_pillar.gan if rule["anchor"] == "gan" else ref_pillar.zhi
            targets = set(rule["table"].get(anchor_value, []))

        if not targets:
            continue

        hit_pillars = [n for n in PILLAR_ORDER if branches[n] in targets]
        if hit_pillars:
            out.append({
                "name": name,
                "reference": rule["reference"],
                "anchor_value": anchor_value,
                "hit_pillars": hit_pillars,
                "hit_branches": [branches[n] for n in hit_pillars],
                "desc": rule.get("desc", ""),
            })
    return out
