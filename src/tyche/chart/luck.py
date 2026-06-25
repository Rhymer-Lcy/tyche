"""大运 / 小运 / 流年 — wraps lunar-python's luck-cycle derivation.

子平 大运: ordered by the month pillar's direction (阳年男 / 阴年女 forward, otherwise
backward); lunar-python's EightChar.getYun(gender) handles it, so this module only reads
the data and attaches 十神.

- 大运 da_yun[i] = {ganzhi, start/end year/age}; index 0 is the pre-起运 stage (童限),
  whose ganzhi may be empty — the real 大运 start at index 1.
- 小运 xiao_yun: the year-by-year 小运 within 童限 (start from the 时柱, step one position
  in the 大运 direction; the 三命通会 method).
- 流年 fleeting_year: a year's 干支 + 十神 (reference follows the 太极点) + the enclosing
  大运 / 小运 / 旬空.

旬空 (xun_kong) is exposed here as deterministic data only, with no 空亡 fortune judgment
(the 空亡 dialectics belong to L3; see docs/rules-L3-spec.md, pending a 命理师 review).

The 禄命 / 星命 schools use a different 纳音-based luck method; that is branched by school
in the L3 rule engine, not here.
"""

from .pillars import Chart
from .ten_gods import ten_god
from ..elements import GAN, ZHI, ZHI_HIDDEN_GAN

# 五虎遁 (month-from-year): year stem -> 正月 (寅月) stem; the twelve months step forward
# from 寅月. Only used for the out-of-range fallback.
_WUHU_START_GAN = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
                   "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
_MONTH_NAMES = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]

# lunar-python: getYun(gender), 1=male, 0=female (verified against known charts)
GENDER_MAP = {"male": 1, "female": 0}


def _yun(chart: Chart):
    return chart.raw_eightchar.getYun(GENDER_MAP[chart.config.gender])


def luck_cycles(chart: Chart, count: int = 10) -> dict:
    """起运 info + 大运 list + 童限 小运.

    da_yun[i] = {ganzhi, start_year, end_year, start_age, end_age, ten_gods}; index 0 is the
    pre-起运 stage (empty ganzhi, ten_gods None). The 十神 reference follows the 太极点.
    """
    yun = _yun(chart)
    ref = chart.reference_gan

    da_yun = []
    for dy in yun.getDaYun()[:count]:
        gz = dy.getGanZhi()
        da_yun.append({
            "ganzhi": gz,
            "start_year": dy.getStartYear(),
            "end_year": dy.getEndYear(),
            "start_age": dy.getStartAge(),
            "end_age": dy.getEndAge(),
            "ten_gods": _ten_gods_of(ref, gz) if len(gz) == 2 else None,
        })

    # 童限 小运: the year-by-year 小运 of the pre-起运 stage (getDaYun()[0]); empty if 起运 at birth
    xiao_yun = [
        {"year": xy.getYear(), "age": xy.getAge(), "ganzhi": xy.getGanZhi(),
         "ten_gods": _ten_gods_of(ref, xy.getGanZhi())}
        for xy in yun.getDaYun()[0].getXiaoYun()
    ]

    return {
        "start_year": yun.getStartYear(),   # age at 起运 (legacy key name kept)
        "is_forward": yun.isForward(),      # True=forward / False=backward
        "da_yun": da_yun,
        "xiao_yun": xiao_yun,
    }


def _ten_gods_of(ref_gan: str, ganzhi: str) -> dict:
    """The 十神 of a 干支 relative to the 太极点: stem + 地支 hidden stems."""
    gan, zhi = ganzhi[0], ganzhi[1]
    return {
        "gan": ten_god(ref_gan, gan),
        "hidden": {g: ten_god(ref_gan, g) for g in ZHI_HIDDEN_GAN.get(zhi, [])},
    }


def fleeting_year(chart: Chart, year: int) -> dict:
    """A Gregorian year's 流年: 干支 + 十神 (reference follows the 太极点) + enclosing 大运 / 小运 / 旬空.

    Prefers the core's LiuNian/XiaoYun (立春 year change handled by the core); when the year is
    out of the derivable range, falls back to the year 干支 directly and leaves 大运/小运 empty.
    """
    yun = _yun(chart)
    ref = chart.reference_gan

    ganzhi = age = xun_kong = dayun_gz = xiaoyun_gz = None
    for dy in yun.getDaYun():
        for ln in dy.getLiuNian():
            if ln.getYear() == year:
                ganzhi, age, xun_kong = ln.getGanZhi(), ln.getAge(), ln.getXunKong()
                dayun_gz = dy.getGanZhi() or None
                break
        if ganzhi is not None:
            for xy in dy.getXiaoYun():
                if xy.getYear() == year:
                    xiaoyun_gz = xy.getGanZhi()
                    break
            break

    if ganzhi is None:   # out of range: take the 立春-based year 干支 directly
        from lunar_python import Solar
        ganzhi = Solar.fromYmd(year, 6, 1).getLunar().getYearInGanZhiByLiChun()

    return {
        "year": year,
        "age": age,
        "ganzhi": ganzhi,
        "ten_gods": _ten_gods_of(ref, ganzhi),
        "xun_kong": xun_kong,
        "dayun": dayun_gz,
        "xiao_yun": xiaoyun_gz,
    }


def fleeting_years(chart: Chart, start_year: int, end_year: int) -> list[dict]:
    """流年 over the closed range [start_year, end_year] (caller bounds it to stay finite)."""
    if end_year < start_year:
        raise ValueError(f"end_year {end_year} < start_year {start_year}")
    return [fleeting_year(chart, y) for y in range(start_year, end_year + 1)]


def _months_by_wuhu(year_gan: str) -> list[str]:
    """五虎遁: derive the twelve month 干支 from the year stem (index 0 = 正月 / 寅月)."""
    start = GAN.index(_WUHU_START_GAN[year_gan])
    yin = ZHI.index("寅")
    return [GAN[(start + i) % 10] + ZHI[(yin + i) % 12] for i in range(12)]


def fleeting_months(chart: Chart, year: int) -> list[dict]:
    """A Gregorian year's twelve 流月: month 干支 + 太极点 十神 + 旬空. index 0 = 正月 (寅月).

    Prefers the core's LiuYue (节气 month change handled by the core); when out of range,
    falls back to 五虎遁 (旬空 left empty).
    """
    yun = _yun(chart)
    ref = chart.reference_gan
    for dy in yun.getDaYun():
        for ln in dy.getLiuNian():
            if ln.getYear() == year:
                return [
                    {
                        "index": ly.getIndex(),
                        "month": ly.getMonthInChinese(),
                        "ganzhi": ly.getGanZhi(),
                        "ten_gods": _ten_gods_of(ref, ly.getGanZhi()),
                        "xun_kong": ly.getXunKong(),
                    }
                    for ly in ln.getLiuYue()
                ]

    from lunar_python import Solar   # out of range: 立春 year stem + 五虎遁
    year_gan = Solar.fromYmd(year, 6, 1).getLunar().getYearInGanZhiByLiChun()[0]
    return [
        {"index": i, "month": _MONTH_NAMES[i], "ganzhi": gz,
         "ten_gods": _ten_gods_of(ref, gz), "xun_kong": None}
        for i, gz in enumerate(_months_by_wuhu(year_gan))
    ]
