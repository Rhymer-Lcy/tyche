"""十二长生 — cross-checked against 禄神 (临官) + fixed-point assertions."""

from tyche import twelve_stage
from tyche.elements import GAN, ZHI

# 禄 = 临官; the "临官" of the 十二长生 table must match this (a strong self-check).
LU = {"甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳", "丁": "午",
      "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}


def test_linguan_equals_lu():
    for g in GAN:
        linguan = [z for z in ZHI if twelve_stage(g, z) == "临官"]
        assert linguan == [LU[g]], f"{g} 临官 should be at {LU[g]}"


def test_specific_stages():
    assert twelve_stage("甲", "亥") == "长生"
    assert twelve_stage("甲", "寅") == "临官"
    assert twelve_stage("甲", "卯") == "帝旺"
    assert twelve_stage("癸", "卯") == "长生"   # yin stem, backward
    assert twelve_stage("癸", "子") == "临官"
    assert twelve_stage("辛", "午") == "病"
