"""七政四余 astronomy layer (M4).

- 四余 (罗睺/计都/月孛): Meeus mean-element formulas, pure Python, zero-dep, always available.
- 七政 (sun/moon/5 planets): built on skyfield (optional `astro` extra) + a JPL ephemeris;
  import on demand via `from tyche.celestial.seven_governors import seven_governors`, so importing
  this package does not fail when skyfield is absent.

命理 interpretation (庙旺/格局/分野/宿度 sidereal zodiac, 罗/计 node assignment, 紫炁 epoch) is a
school-dependent layer; this layer only gives ephemeris-verifiable deterministic quantities.
"""

from .four_residues import four_residues
from .zodiac import zodiac_position

__all__ = ["four_residues", "zodiac_position"]
