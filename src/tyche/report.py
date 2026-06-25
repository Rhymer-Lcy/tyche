"""Single orchestration: one cast() collapses charting + 十神 + 大运 + rule analysis into one ChartReport.

This is the engine's single public entry point — the SaaS API, the reading LLM, and RAG retrieval
all read from ChartReport instead of calling build_chart/chart_ten_gods/luck_cycles/analyze separately.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .chart.config import ChartConfig
from .chart.pillars import Chart, build_chart
from .chart.ten_gods import chart_ten_gods
from .chart.luck import luck_cycles
from .rules import analyze


@dataclass
class ChartReport:
    """The complete structured result of one chart (deterministic layer + rule layer)."""

    chart: Chart
    ten_gods: dict
    luck: dict
    strength: dict
    pattern: dict
    relations: list
    shensha: list

    # —— convenience pass-throughs ——
    @property
    def config(self) -> ChartConfig:
        return self.chart.config

    @property
    def reference_gan(self) -> str:
        return self.chart.reference_gan

    def to_dict(self) -> dict:
        c = self.chart
        return {
            "config": {
                "reference_pillar": c.config.reference_pillar,
                "school": c.config.school,
                "pattern_school": getattr(c.config, "pattern_school", "ziping"),
                "gender": c.config.gender,
                "longitude": c.config.longitude,
            },
            "solar_input": c.solar_input.isoformat(),
            "solar_effective": c.solar_effective.isoformat(),
            "pillars": {
                name: {
                    "ganzhi": p.ganzhi,
                    "nayin": p.nayin,
                    "hidden_gans": p.hidden_gans,
                    "ten_gods": self.ten_gods[name],
                }
                for name, p in c.pillars.items()
            },
            "minggong": c.minggong,
            "shengong": c.shengong,
            "taiyuan": c.taiyuan,
            "reference_gan": c.reference_gan,
            "strength": self.strength,
            "pattern": self.pattern,
            "relations": self.relations,
            "shensha": self.shensha,
            "luck": self.luck,
        }


def cast(dt: datetime, config: Optional[ChartConfig] = None) -> ChartReport:
    """Chart and run all rules from a Gregorian instant + config; return a ChartReport."""
    chart = build_chart(dt, config or ChartConfig())
    rules = analyze(chart)
    return ChartReport(
        chart=chart,
        ten_gods=chart_ten_gods(chart),
        luck=luck_cycles(chart),
        strength=rules["strength"],
        pattern=rules["pattern"],
        relations=rules["relations"],
        shensha=rules["shensha"],
    )
