"""格局 — month-command 取格 (子平).

Rules:
  - month branch = DM's 临官 -> 建禄格; month branch = DM's 帝旺 -> 月刃格 (羊刃).
  - otherwise pick by which month-branch hidden stems are exposed among the other stems.
    比劫 forms no pattern (folded into 建禄/月劫), so candidates must drop any exposed
    比肩/劫财 (子平真诠's eight patterns use "建禄月劫"; 三命通会 treats it as a 别格).
  - when the 本气 is in command but not exposed while a middle/residual qi exposes another
    god, which pattern to take is school-dependent, via config.pattern_school:
      - ziping (default, 子平真诠): take the exposed other-god pattern.
      - gufa_dangling (古法当令): keep the in-command 本气 as the main pattern, exposed gods as 兼.

Note: 取格 is already school-sensitive; whether a pattern is formed/broken and its grade belong
to the reading layer — this module only fixes the "月令 pattern god".
(Rules per docs/rules-L3-spec.md; verified against 三命通会/玉井奥诀/星命抉古录 + 子平真诠.)
"""

from .changsheng import twelve_stage
from ..chart.ten_gods import ten_god
from ..elements import ZHI_HIDDEN_GAN

_BIJIE = {"比肩", "劫财"}


def chart_pattern(chart) -> dict:
    dm = chart.day.gan
    month_zhi = chart.month.zhi
    hidden = ZHI_HIDDEN_GAN[month_zhi]          # [本气, 中气, 余气]
    other_stems = [chart.year.gan, chart.month.gan, chart.hour.gan]  # excludes the day stem
    stage = twelve_stage(dm, month_zhi)
    school = getattr(chart.config, "pattern_school", "ziping")

    # 建禄 / 月刃 special-case (比劫 form no separate pattern)
    if stage == "临官":
        return _result("建禄格", "月支为日主临官(禄)", None, [], hidden, stage)
    if stage == "帝旺":
        return _result("月刃格", "月支为日主帝旺(羊刃)", None, [], hidden, stage)

    benqi = hidden[0]
    # exposed other gods (drop 比劫: they form no pattern); keep hidden-stem 本→中→余 order
    transmitted = [g for g in hidden if g in other_stems]
    eligible = [g for g in transmitted if ten_god(dm, g) not in _BIJIE]

    if school == "gufa_dangling":
        # 古法: in-command 本气 first (exposed -> 本气 pattern; if not, still take the in-command
        # 本气 and treat exposed gods as 兼)
        if benqi in eligible:
            ge_gan, basis, jian = benqi, "月令本气透干(古法当令)", []
        else:
            ge_gan, basis, jian = benqi, "月令本气当令(古法,未透亦取本气)", eligible
    else:
        # 子平真诠 (default): 本气 exposed -> 本气; not exposed but a non-比劫 is exposed -> take it;
        # otherwise fall back to 本气
        jian = []
        if benqi in eligible:
            ge_gan, basis = benqi, "月令本气透干"
        elif eligible:
            ge_gan, basis = eligible[0], "月令本气不透,取透出之他神(子平真诠)"
        else:
            ge_gan, basis = benqi, "月令本气(无合格透干,取本气当令)"

    return _result(ten_god(dm, ge_gan) + "格", basis, ge_gan, transmitted, hidden, stage,
                   jian_shen=jian, school=school)


def _result(pattern, basis, ge_gan, transmitted, hidden, stage, jian_shen=None, school="ziping"):
    return {
        "pattern": pattern,
        "basis": basis,
        "ge_gan": ge_gan,
        "jian_shen": jian_shen or [],     # 兼神 (exposed other gods) under the 古法当令 school
        "transmitted": transmitted,
        "month_hidden": hidden,
        "day_master_stage": stage,
        "pattern_school": school,
    }
