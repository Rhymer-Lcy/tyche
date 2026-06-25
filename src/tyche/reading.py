"""Reading-prompt builder: turn a ChartReport into the {system, user} pair fed to an LLM.

Design: the chart facts are computed by the deterministic engine; the prompt marks them as
authoritative and tells the LLM not to recompute, only to interpret. Once RAG is wired in,
append the retrieved classical passages to the 【经典依据】 section of the user message
(see docs §8/§10). The prompt body itself stays Chinese — it instructs a Chinese-命理 reading.
"""

from .report import ChartReport

_PNAME = {"year": "年", "month": "月", "day": "日", "hour": "时"}

SYSTEM = """你是一位严谨的命理师。下面给你的命盘是由确定性程序排定的【既成事实】,请严格遵守:
1. 不要重新排盘、不要重算四柱/十神/神煞/旺衰/格局——直接采信给定数据(你重算极易出错)。
2. 只做"解读与组织语言":基于给定旺衰、格局、十神、神煞、刑冲合害,推演命主性情、能力倾向与所问之事,逻辑要能回溯到具体命盘要素("因为盘上 X,所以 Y")。
3. 分点作答,先总纲后分项;用词专业但让外行能懂。
4. 不确定处如实说"此点存疑/需结合更多信息",不要硬断、不要编造经典原文。
5. 结尾附:本结果为传统文化娱乐参考,不构成医疗/投资/婚姻等决策依据。
（接入知识库后会额外收到【经典依据】片段,届时断语须引用其出处;现无片段,仅凭命盘结构作答。）"""


def _cols(pillars: list) -> str:
    return "".join(_PNAME[p] for p in pillars)


def _fmt_ten_gods(gods: dict) -> str:
    parts = []
    for name, label in _PNAME.items():
        g = gods[name]
        hidden = "、".join(f"{k}={v}" for k, v in g["hidden"].items())
        parts.append(f"{label}干 {g['gan']}(藏干 {hidden})")
    return ";".join(parts)


def _fmt_relations(rels: list) -> str:
    if not rels:
        return "无明显刑冲合害"
    return ";".join(
        f"{r['type']}{('(' + r['note'] + ')') if r.get('note') else ''}:{''.join(r['items'])}[{_cols(r['pillars'])}柱]"
        for r in rels
    )


def _fmt_shensha(ss: list) -> str:
    return "、".join(f"{s['name']}({_cols(s['hit_pillars'])})" for s in ss) if ss else "无"


def build_reading_prompt(report: ChartReport, question: str = "综合命理") -> dict:
    c = report.chart
    st, pt = report.strength, report.pattern
    direction = "顺行" if report.luck["is_forward"] else "逆行"
    dayun = "  ".join(
        f"{d['ganzhi']}·{d['ten_gods']['gan']}({d['start_age']}岁)"
        for d in report.luck["da_yun"][1:7]
    )

    user = f"""【命主】{c.config.gender} | 钟表 {c.solar_input:%Y-%m-%d %H:%M} → 真太阳时 {c.solar_effective:%Y-%m-%d %H:%M} | 太极点={c.config.reference_pillar}
【四柱】年 {c.year.ganzhi}({c.year.nayin}) 月 {c.month.ganzhi}({c.month.nayin}) 日 {c.day.ganzhi}({c.day.nayin}) 时 {c.hour.ganzhi}({c.hour.nayin})
【日主】{st['day_master']}{st['day_master_wuxing']};旺衰:{st['level']}(扶 {st['support']} / 耗 {st['drain']},月令十二长生={st['month_stage']})
【格局】{pt['pattern']}({pt['basis']})
【十神】{_fmt_ten_gods(report.ten_gods)}
【神煞】{_fmt_shensha(report.shensha)}
【刑冲合害】{_fmt_relations(report.relations)}
【命宫/身宫/胎元】{c.minggong} / {c.shengong} / {c.taiyuan}
【大运】{report.luck['start_year']} 岁起运,{direction};{dayun}
【提问】{question}

请据此作答。"""
    return {"system": SYSTEM, "user": user}
