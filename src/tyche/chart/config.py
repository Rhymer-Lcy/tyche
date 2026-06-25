"""Charting config — the 太极点 switch lives here.

reference_pillar is the top-level switch that runs through the 十神 reference, 旺衰 origin,
神煞 base, luck cycles, and other branches (see docs/architecture.md §3). M1 implements the
十神-reference branch first; the rest are wired in as the L3 rule engine grows.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class ChartConfig:
    # 太极点: day = 子平 (day stem as the self) / year = 禄命星命 (year pillar as the root)
    reference_pillar: Literal["day", "year"] = "day"
    # School: ziping=子平 / luming=禄命 / xingming=星命 (the latter two share the year 太极点; school
    # subdivides within it). Orthogonal to reference_pillar: this picks the school, that picks the
    # 太极点. Used by the rule engine later; in M1 it is only a label.
    school: Literal["ziping", "luming", "xingming"] = "ziping"
    # Gender: needed for 大运 direction (阳年男 / 阴年女 go forward, otherwise backward)
    gender: Literal["male", "female"] = "male"
    # Birth longitude (east positive). If given, apply true solar time; if None, chart by clock time.
    longitude: Optional[float] = None
    use_true_solar_time: bool = True
    # Overlay charts: 命宫/胎元/身宫 etc. (命宫/胎元 already available in M1; reserved extension point)
    overlays: list[str] = field(default_factory=list)
    # 取格 school: ziping=子平真诠 (if 本气 is not exposed, take the exposed other 十神) /
    # gufa_dangling=古法当令 (the 本气 in command takes priority)
    pattern_school: Literal["ziping", "gufa_dangling"] = "ziping"
    # 取格 priority when several stems are exposed: sheng_order=hidden-stem 本→中→余 /
    # qiang_weak=by strength (not yet implemented; placeholder)
    transmit_priority: Literal["sheng_order", "qiang_weak"] = "sheng_order"
