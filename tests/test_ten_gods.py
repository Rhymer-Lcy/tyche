"""十神 table unit tests — verified directly from 五行 generation/control + same/different 阴阳."""

from tyche import ten_god


def test_ten_god_rules():
    # take 甲 (yang 木) as the self
    assert ten_god("甲", "甲") == "比肩"   # same 五行, same 阴阳
    assert ten_god("甲", "乙") == "劫财"   # same 五行, different 阴阳
    assert ten_god("甲", "丙") == "食神"   # I generate (木→火), same 阴阳
    assert ten_god("甲", "丁") == "伤官"   # I generate, different 阴阳
    assert ten_god("甲", "壬") == "偏印"   # generates me (水→木), same 阴阳
    assert ten_god("甲", "癸") == "正印"   # generates me, different 阴阳
    assert ten_god("甲", "戊") == "偏财"   # I control (木→土), same 阴阳
    assert ten_god("甲", "己") == "正财"   # I control, different 阴阳
    assert ten_god("甲", "庚") == "七杀"   # controls me (金→木), same 阴阳
    assert ten_god("甲", "辛") == "正官"   # controls me, different 阴阳


def test_ten_god_yin_reference():
    # take 辛 (yin 金) as the self: 庚 (yang 金) same 五行, different 阴阳 -> 劫财
    assert ten_god("辛", "庚") == "劫财"
    assert ten_god("辛", "壬") == "伤官"   # 金 generates 水, different 阴阳
    assert ten_god("辛", "乙") == "偏财"   # 金 controls 木, same 阴阳 (辛 yin, 乙 yin)
