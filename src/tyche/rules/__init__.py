"""L3 rule engine: 神煞, plus 刑冲合害会破 relations.

tyche's core differentiator. Two principles:
  - 神煞 tables live in data/shensha.yaml, each tagged anchor/reference, routed by the 太极点 (day/year);
  - relations (刑冲合害会破) are structural rules, in relations.py.

Entry point: analyze(chart) -> {"relations", "shensha", "strength", "pattern"}
"""

from ..chart.pillars import Chart
from .relations import detect_branch_relations, detect_stem_relations
from .shensha import detect_shensha
from .changsheng import twelve_stage
from .strength import chart_strength
from .pattern import chart_pattern


def analyze(chart: Chart) -> dict:
    """Run all rules on one chart.

    relations/shensha route by the 太极点 (reference_pillar); strength/pattern are 子平
    day-master analysis (always centred on the day master). 禄命's 纳音 strength is M3.
    """
    branches = {name: p.zhi for name, p in chart.pillars.items()}
    stems = {name: p.gan for name, p in chart.pillars.items()}
    return {
        "relations": detect_stem_relations(stems) + detect_branch_relations(branches),
        "shensha": detect_shensha(chart),
        "strength": chart_strength(chart),   # 子平 day-master 旺衰
        "pattern": chart_pattern(chart),     # month-command 取格
    }


__all__ = [
    "analyze",
    "detect_branch_relations",
    "detect_stem_relations",
    "detect_shensha",
    "twelve_stage",
    "chart_strength",
    "chart_pattern",
]
