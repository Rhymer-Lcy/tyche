"""Ephemeris loading (skyfield). 七政 positions need a JPL ephemeris kernel (default de421.bsp, covering 1899-2053).

Ephemeris directory priority: explicit path > the TYCHE_EPHEMERIS_DIR env var > ~/.tyche/ephemeris.
On first use, if the kernel is absent locally, skyfield downloads it (~17 MB). The result is cached
per directory to avoid reloading.

skyfield is an optional dependency (`pip install -e ".[astro]"`); importing this module raises
ImportError when it is not installed.
"""

import os
from functools import lru_cache

DEFAULT_KERNEL = "de421.bsp"


def _ephemeris_dir(path: str | None) -> str:
    return (
        path
        or os.environ.get("TYCHE_EPHEMERIS_DIR")
        or os.path.join(os.path.expanduser("~"), ".tyche", "ephemeris")
    )


@lru_cache(maxsize=None)
def get_ephemeris(path: str | None = None, kernel: str = DEFAULT_KERNEL):
    """Return (ephemeris, timescale). Cached by (path, kernel)."""
    from skyfield.api import Loader

    loader = Loader(_ephemeris_dir(path))
    return loader(kernel), loader.timescale()
