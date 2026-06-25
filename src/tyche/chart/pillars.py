"""Four-pillar charting — wraps lunar-python (6tail), producing tyche's own Chart.

lunar-python handles the deterministic calendar/astronomy (节气-based month, 干支, 纳音,
藏干, 命宫/胎元); tyche adds true-solar-time correction (at the input) and a configurable
太极点 (the 十神 layer, see ten_gods).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from lunar_python import Solar

from .config import ChartConfig
from ..calendar.true_solar_time import apply_true_solar_time


@dataclass
class Pillar:
    """One pillar: 天干, 地支, 纳音, and the 地支 hidden stems."""

    gan: str
    zhi: str
    nayin: str
    hidden_gans: list[str] = field(default_factory=list)

    @property
    def ganzhi(self) -> str:
        return self.gan + self.zhi

    def __str__(self) -> str:
        return self.ganzhi


@dataclass
class Chart:
    """One chart. raw_eightchar keeps the original lunar-python object for 大运 / extensions."""

    config: ChartConfig
    solar_input: datetime       # original clock time
    solar_effective: datetime   # after true-solar-time correction (used for charting)
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar
    minggong: str               # 命宫
    shengong: str               # 身宫
    taiyuan: str                # 胎元
    raw_eightchar: object = field(repr=False, default=None)

    @property
    def pillars(self) -> dict[str, Pillar]:
        return {"year": self.year, "month": self.month, "day": self.day, "hour": self.hour}

    @property
    def reference_gan(self) -> str:
        """The reference 天干 for the 太极点: 子平 = day stem, 禄命星命 = year stem."""
        return self.day.gan if self.config.reference_pillar == "day" else self.year.gan


def build_chart(dt: datetime, config: Optional[ChartConfig] = None) -> Chart:
    """Build a chart from a Gregorian instant + config."""
    config = config or ChartConfig()

    effective = dt
    if config.use_true_solar_time and config.longitude is not None:
        effective = apply_true_solar_time(dt, config.longitude)

    solar = Solar.fromYmdHms(
        effective.year, effective.month, effective.day,
        effective.hour, effective.minute, effective.second,
    )
    ec = solar.getLunar().getEightChar()

    def mk(gan, zhi, nayin, hide) -> Pillar:
        return Pillar(gan=gan, zhi=zhi, nayin=nayin, hidden_gans=list(hide))

    return Chart(
        config=config,
        solar_input=dt,
        solar_effective=effective,
        year=mk(ec.getYearGan(), ec.getYearZhi(), ec.getYearNaYin(), ec.getYearHideGan()),
        month=mk(ec.getMonthGan(), ec.getMonthZhi(), ec.getMonthNaYin(), ec.getMonthHideGan()),
        day=mk(ec.getDayGan(), ec.getDayZhi(), ec.getDayNaYin(), ec.getDayHideGan()),
        hour=mk(ec.getTimeGan(), ec.getTimeZhi(), ec.getTimeNaYin(), ec.getTimeHideGan()),
        minggong=ec.getMingGong(),
        shengong=ec.getShenGong(),
        taiyuan=ec.getTaiYuan(),
        raw_eightchar=ec,
    )
