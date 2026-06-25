"""Five-element constants: 天干, 地支, 五行, 阴阳, generation/control, hidden stems.

These are tyche's own truth tables. Logic such as 十神 builds on them, which reduces
the 太极点 switch (referencing the day stem or the year stem) to a single parameter.
"""

# the ten 天干 (heavenly stems)
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# the twelve 地支 (earthly branches)
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干 -> 五行
GAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 天干 -> 阴阳 (甲丙戊庚壬 are 阳, 乙丁己辛癸 are 阴)
GAN_YINYANG = {
    "甲": "阳", "丙": "阳", "戊": "阳", "庚": "阳", "壬": "阳",
    "乙": "阴", "丁": "阴", "己": "阴", "辛": "阴", "癸": "阴",
}

# 五行 generation cycle: 木→火→土→金→水→木
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行 control cycle: 木 controls 土, 土 controls 水, 水 controls 火, 火 controls 金, 金 controls 木
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 地支 hidden stems (primary / middle / residual qi); the standard charting table
ZHI_HIDDEN_GAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 十二长生 stages in 长生→养 order; yang stems run forward (branch +1), yin stems backward (-1).
# The 长生 start point is self-consistent with 禄 (临官) and cross-checks the 禄神 table in shensha.yaml.
TWELVE_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
CHANGSHENG_START = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",   # yang stems (forward)
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",   # yin stems (backward)
}
