"""Golden set: lock charting output with verified charts to guard against refactor regressions.

Each case only asserts the fields present in its expect block (partial-pillar cases are allowed,
making boundary cases easy to add).
"""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from tyche import build_chart, ChartConfig, chart_ten_gods, luck_cycles

CASES = yaml.safe_load((Path(__file__).parent / "golden" / "cases.yaml").read_text(encoding="utf-8"))


def _build(case, ref="day"):
    dt = datetime.strptime(case["datetime"], "%Y-%m-%d %H:%M")
    cfg = ChartConfig(
        reference_pillar=ref,
        gender=case.get("gender", "male"),
        longitude=case.get("longitude"),
    )
    return build_chart(dt, cfg)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_golden(case):
    exp = case["expect"]
    chart = _build(case, "day")

    if "pillars" in exp:
        for name, gz in exp["pillars"].items():
            assert chart.pillars[name].ganzhi == gz, f"{name} pillar"
    if "nayin" in exp:
        for name, ny in exp["nayin"].items():
            assert chart.pillars[name].nayin == ny, f"{name} nayin"
    if "minggong" in exp:
        assert chart.minggong == exp["minggong"]
    if "taiyuan" in exp:
        assert chart.taiyuan == exp["taiyuan"]
    if "ten_gods_day" in exp:
        g = chart_ten_gods(chart)  # 太极点 = day
        for name, god in exp["ten_gods_day"].items():
            assert g[name]["gan"] == god, f"{name} 十神 (day 太极点)"
    if "ten_gods_year" in exp:
        gy = chart_ten_gods(_build(case, "year"))  # 太极点 = year
        for name, god in exp["ten_gods_year"].items():
            assert gy[name]["gan"] == god, f"{name} 十神 (year 太极点)"
    if "first_dayun" in exp:
        luck = luck_cycles(chart)
        assert luck["da_yun"][1]["ganzhi"] == exp["first_dayun"]
