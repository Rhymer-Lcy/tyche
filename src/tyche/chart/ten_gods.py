"""十神 — tyche's own implementation, 太极点-configurable.

A 十神 is a table lookup over (reference stem vs target stem): the 五行 generation/control
relation plus same/different 阴阳:
  same 五行:    比肩 (same 阴阳) / 劫财 (different)
  I generate:   食神 (same) / 伤官 (different)
  generates me: 偏印 (same) / 正印 (different)
  I control:    偏财 (same) / 正财 (different)
  controls me:  七杀 (same) / 正官 (different)

The reference stem = chart.reference_gan, decided by ChartConfig.reference_pillar
(子平 takes the day stem, 禄命星命 takes the year stem) — this is how the 太极点 switch
lands in the 十神 layer.
"""

from .pillars import Chart
from ..elements import GAN_WUXING, GAN_YINYANG, WUXING_SHENG, WUXING_KE


def ten_god(reference_gan: str, target_gan: str) -> str:
    """Take reference_gan as the self; return target_gan's 十神 relative to it."""
    rw = GAN_WUXING[reference_gan]
    tw = GAN_WUXING[target_gan]
    same_yy = GAN_YINYANG[reference_gan] == GAN_YINYANG[target_gan]

    if rw == tw:                       # same 五行
        return "比肩" if same_yy else "劫财"
    if WUXING_SHENG[rw] == tw:         # I generate
        return "食神" if same_yy else "伤官"
    if WUXING_SHENG[tw] == rw:         # generates me
        return "偏印" if same_yy else "正印"
    if WUXING_KE[rw] == tw:            # I control
        return "偏财" if same_yy else "正财"
    if WUXING_KE[tw] == rw:            # controls me
        return "七杀" if same_yy else "正官"
    raise ValueError(f"cannot determine 十神: {reference_gan} -> {target_gan}")


def chart_ten_gods(chart: Chart) -> dict:
    """All 十神 of the chart (stems + 地支 hidden stems); the reference follows the 太极点.

    The reference pillar's own stem is always 比肩; it is labelled as the self
    (日元 / 年元) to set it apart.
    """
    ref = chart.reference_gan
    ref_pillar_name = "day" if chart.config.reference_pillar == "day" else "year"
    self_label = "日元" if ref_pillar_name == "day" else "年元"

    result = {}
    for name, p in chart.pillars.items():
        gan_god = self_label if (name == ref_pillar_name) else ten_god(ref, p.gan)
        result[name] = {
            "gan": gan_god,
            "hidden": {g: ten_god(ref, g) for g in p.hidden_gans},
        }
    return result
