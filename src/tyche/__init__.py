"""tyche — AI 命理 charting core.

Methodology: deterministic charting + symbolic knowledge (RAG) + an LLM for wording. This
package is the deterministic layer only (calendar/astronomy + charting); it contains no LLM/RAG.

The two paradigms are routed by ChartConfig.reference_pillar:
- "day"   子平 (the day stem as the 太极点 / self)
- "year"  禄命星命 (the year pillar as the 太极点)
"""

from .chart.config import ChartConfig
from .chart.pillars import Chart, Pillar, build_chart
from .chart.ten_gods import ten_god, chart_ten_gods
from .chart.luck import luck_cycles, fleeting_year, fleeting_years, fleeting_months
from .rules import analyze, twelve_stage, chart_strength, chart_pattern
from .report import cast, ChartReport
from .reading import build_reading_prompt
from .render import render_chart

__version__ = "0.1.0"

__all__ = [
    "ChartConfig",
    "Chart",
    "Pillar",
    "build_chart",
    "ten_god",
    "chart_ten_gods",
    "luck_cycles",
    "fleeting_year",
    "fleeting_years",
    "fleeting_months",
    "analyze",
    "twelve_stage",
    "chart_strength",
    "chart_pattern",
    "cast",
    "ChartReport",
    "build_reading_prompt",
    "render_chart",
]
