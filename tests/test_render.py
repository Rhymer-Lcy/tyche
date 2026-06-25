"""Human-readable chart-card renderer."""

from datetime import datetime

from tyche import cast, ChartConfig, render_chart


def _card(ref="day"):
    return render_chart(cast(datetime(1990, 6, 15, 14, 30),
                             ChartConfig(gender="male", longitude=116.40, reference_pillar=ref)))


def test_card_sections_and_facts():
    card = _card()
    for marker in ("命盘", "【四柱】", "【命宫/身宫/胎元】", "【旺衰】", "【格局】", "【大运】"):
        assert marker in card, marker
    assert "命宫/身宫/胎元】庚辰 / 戊寅 / 癸酉" in card
    assert "日柱 辛亥  十神 日元" in card          # the 日元 self-label + 藏干 十神
    assert "七杀格" in card
    assert "癸未·食神" in card                      # 大运 carries 十神
    assert "童限小运】丙申(1岁)" in card           # one step forward from 时柱
    assert "真太阳时 1990-06-15 14:15" in card     # longitude offset -14.4 min


def test_card_taiji_switch_changes_school_label():
    assert "子平·日太极" in _card("day")
    assert "禄命星命·年太极" in _card("year")
