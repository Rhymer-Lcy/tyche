"""Render a ChartReport into a human-readable plain-text chart card.

For people who do not read code/JSON (the 命理师, the subject), and handy for eyeballing the
chart while debugging. Uses a label-per-pillar layout that does not rely on CJK monospace
alignment (renders stably across fonts). 神煞 / 刑冲合害 reuse reading.py's formatting for
consistent wording. The card body itself stays Chinese — it is a 命理 card.
"""

from .reading import _fmt_relations, _fmt_shensha
from .report import ChartReport

_PILLARS = (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱"))
_SCHOOL = {"day": "子平·日太极", "year": "禄命星命·年太极"}


def render_chart(report: ChartReport) -> str:
    c = report.chart
    cfg = c.config
    tg = report.ten_gods
    st, pt = report.strength, report.pattern
    luck = report.luck
    gender = "男" if cfg.gender == "male" else "女"

    out: list[str] = []
    out.append("═══════ 命盘 ═══════")
    out.append(
        f"命主:{gender}  |  钟表 {c.solar_input:%Y-%m-%d %H:%M}"
        f" → 真太阳时 {c.solar_effective:%Y-%m-%d %H:%M}"
        f"  |  太极点 {_SCHOOL[cfg.reference_pillar]}"
    )
    out.append("")
    out.append("【四柱】")
    for key, label in _PILLARS:
        p = c.pillars[key]
        g = tg[key]
        hidden = "·".join(f"{k}({v})" for k, v in g["hidden"].items())
        out.append(f"  {label} {p.ganzhi}  十神 {g['gan']}  纳音 {p.nayin}  藏干 {hidden}")
    out.append("")
    out.append(f"【命宫/身宫/胎元】{c.minggong} / {c.shengong} / {c.taiyuan}")
    out.append(
        f"【旺衰】日主 {st['day_master']}({st['day_master_wuxing']}) {st['level']}"
        f"(扶 {st['support']} / 耗 {st['drain']},月令长生={st['month_stage']})"
    )
    out.append(f"【格局】{pt['pattern']}({pt['basis']})")
    out.append(f"【神煞】{_fmt_shensha(report.shensha)}")
    out.append(f"【刑冲合害】{_fmt_relations(report.relations)}")
    out.append("")
    direction = "顺行" if luck["is_forward"] else "逆行"
    out.append(f"【大运】{luck['start_year']} 岁起运,{direction}")
    for d in luck["da_yun"][1:]:
        out.append(
            f"  {d['ganzhi']}·{d['ten_gods']['gan']}"
            f"  {d['start_age']}-{d['end_age']}岁  {d['start_year']}-{d['end_year']}"
        )
    if luck["xiao_yun"]:
        xy = "  ".join(f"{x['ganzhi']}({x['age']}岁)" for x in luck["xiao_yun"])
        out.append(f"【童限小运】{xy}")
    return "\n".join(out)
