"""Day-master 旺衰 (strength) — 子平 fuyi (support/drain) scoring (tyche v1, a transparent take).

Note: 旺衰 is a loosely-defined layer with many schools and disagreement. This module gives a
transparent, testable, explicit-weight support/drain score, returning a strength level plus a
full breakdown — not "the one true answer". Finer 旺衰/调候/通关 judgments are left to the
reading (RAG+LLM) layer on top of this structured result.

Method (centred on the day master DM, 子平):
  1. Month command: DM's 十二长生 stage in the month branch -> in-command adjustment
     (临官/帝旺 strongest, 绝/胎 weakest).
  2. Roots + support/drain: per pillar (stem + branch 本气) classify by 五行 relation as
     "扶" (same-as-me / generates-me = 比劫 / 印) or "耗" (I-generate / I-control / controls-me
     = 食伤 / 财 / 官杀), accumulated with positional weights.
  3. Support ratio -> level. Weights and thresholds are the constants below; to change school,
     change only these.
"""

from .changsheng import twelve_stage
from ..elements import GAN_WUXING, WUXING_SHENG, ZHI_HIDDEN_GAN

# Stems carry no positional weight (all 1.0; the day stem is the DM and is excluded);
# positional weight applies only to branches.
STEM_WEIGHT = {"year": 1.0, "month": 1.0, "hour": 1.0}
# Branch positional weight: the month command is heaviest, the day branch next.
BRANCH_WEIGHT = {"month": 3.0, "day": 2.0, "year": 1.5, "hour": 1.5}
# In-command adjustment (DM's 长生 stage in the month branch -> added to 扶/耗).
STAGE_MODIFIER = {
    "临官": 2.0, "帝旺": 2.0, "长生": 1.0, "冠带": 1.0, "墓": 0.5,
    "衰": 0.0, "养": 0.0, "沐浴": 0.0, "病": -1.0, "死": -1.0, "胎": -1.0, "绝": -2.0,
}
# Level thresholds on the support ratio = support / (support + drain).
LEVELS = [(0.65, "强"), (0.55, "偏强"), (0.45, "中和"), (0.35, "偏弱"), (0.0, "弱")]


def _supports(dm_wx: str, other_wx: str) -> bool:
    """Whether other supports the DM: same-as-me (比劫) or generates-me (印)."""
    return other_wx == dm_wx or WUXING_SHENG[other_wx] == dm_wx


def chart_strength(chart) -> dict:
    """Compute day-master 旺衰 (子平). Returns the level + a transparent breakdown."""
    dm = chart.day.gan
    dm_wx = GAN_WUXING[dm]
    contributions = []
    support = 0.0
    drain = 0.0

    # stems (year/month/hour; the day stem itself is excluded)
    for name in ("year", "month", "hour"):
        gan = chart.pillars[name].gan
        wx = GAN_WUXING[gan]
        w = STEM_WEIGHT[name]
        kind = "扶" if _supports(dm_wx, wx) else "耗"
        if kind == "扶":
            support += w
        else:
            drain += w
        contributions.append({"source": f"{name}干", "item": gan, "wuxing": wx, "kind": kind, "weight": w})

    # branch 本气 (primary qi)
    for name in ("year", "month", "day", "hour"):
        zhi = chart.pillars[name].zhi
        benqi = ZHI_HIDDEN_GAN[zhi][0]
        wx = GAN_WUXING[benqi]
        w = BRANCH_WEIGHT[name]
        kind = "扶" if _supports(dm_wx, wx) else "耗"
        if kind == "扶":
            support += w
        else:
            drain += w
        contributions.append({"source": f"{name}支本气", "item": benqi, "wuxing": wx, "kind": kind, "weight": w})

    # month-command adjustment
    month_stage = twelve_stage(dm, chart.month.zhi)
    mod = STAGE_MODIFIER[month_stage]
    if mod >= 0:
        support += mod
    else:
        drain += -mod

    total = support + drain
    ratio = support / total if total else 0.0
    level = next(name for thr, name in LEVELS if ratio >= thr)

    return {
        "day_master": dm,
        "day_master_wuxing": dm_wx,
        "month_stage": month_stage,      # DM's 十二长生 stage in the month branch (in command or not)
        "support": round(support, 2),
        "drain": round(drain, 2),
        "ratio": round(ratio, 3),
        "level": level,                  # one of: 强 / 偏强 / 中和 / 偏弱 / 弱
        "contributions": contributions,
        "method": "ziping-fuyi-v1",
    }
