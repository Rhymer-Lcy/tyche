"""黄道十二宫 placement (tropical, of-date): ecliptic longitude -> sign + degree-in-sign + 果老 branch palace.

Convention: the tropical zodiac (vernal point 0° = 白羊 0°), consistent with 节气-based sign entry.
Note: the 果老星宗 tradition also has a sidereal (宿度) placement; the two differ by ~one sign due to
precession — a school convention. This layer gives only the tropical placement and leaves the
sidereal one to the 命理 layer (see docs).
"""

# 黄道十二宫 (from 0°, every 30°)
_SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
          "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
# 果老 十二宫-to-branch mapping (中气过宫): 戌=白羊 (降娄) … 亥=双鱼 (娵訾)
_SIGN_BRANCH = ["戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥"]


def zodiac_position(lon: float) -> dict:
    """Ecliptic longitude (deg) -> {lon, sign, sign_index, degree (0-30 in sign), palace_branch}."""
    lon %= 360.0
    i = int(lon // 30)
    return {
        "lon": round(lon, 3),
        "sign": _SIGNS[i],
        "sign_index": i,
        "degree": round(lon - i * 30, 2),
        "palace_branch": _SIGN_BRANCH[i],
    }
