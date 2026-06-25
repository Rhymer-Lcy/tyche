"""十二长生: which stage a 天干 is in at a given 地支 (长生/沐浴/.../墓/绝/胎/养).

A deterministic table lookup (from the 长生 start point and 阴阳 direction in elements);
the basis for 旺衰.
"""

from ..elements import ZHI, GAN_YINYANG, TWELVE_STAGES, CHANGSHENG_START


def twelve_stage(gan: str, zhi: str) -> str:
    """The 十二长生 stage of 天干 gan at 地支 zhi."""
    start = ZHI.index(CHANGSHENG_START[gan])
    step = 1 if GAN_YINYANG[gan] == "阳" else -1
    offset = ((ZHI.index(zhi) - start) * step) % 12
    return TWELVE_STAGES[offset]
