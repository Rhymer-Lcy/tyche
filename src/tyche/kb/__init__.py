"""Knowledge-base construction (M2): MinerU/pandoc text -> A/B/C triage -> chunks with metadata.

This package holds only the deterministic part (loading, parsing, page-number restoration);
A/B/C triage and metadata tagging are LLM work (workflow / manual), not here.

The four books come from different sources: PDFs go through MinerU into json, docx through
pandoc into md. `load_book(slug)` dispatches by directory (mineru/ first, then pandoc/), so
downstream only ever sees a unified list of Blocks.
"""

import os
from pathlib import Path
from typing import Union

from .blocks import Block
from .mineru_loader import load_mineru_json, load_mineru_book, part_offset
from .pandoc_loader import load_pandoc_md

__all__ = [
    "Block",
    "load_book",
    "load_mineru_json",
    "load_mineru_book",
    "load_pandoc_md",
    "part_offset",
]


def _default_base() -> str:
    """Corpus root: the TYCHE_KB_DIR env var if set, else docs_local relative to the CWD."""
    return os.environ.get("TYCHE_KB_DIR") or "docs_local"


def load_book(slug: str, base: Union[str, Path, None] = None) -> list[Block]:
    """Dispatch a loader by the book directory's actual artifacts; return a unified Block list.

    mineru/*.json (PDF source) takes priority; otherwise pandoc/*.md (docx source). base
    defaults to _default_base() (TYCHE_KB_DIR, or docs_local relative to the CWD); docs_local
    is the gitignored local corpus, absent from a clone, so point base/env at your own copy.
    """
    base = base if base is not None else _default_base()
    root = Path(base) / slug
    mineru = root / "mineru"
    if mineru.is_dir() and any(mineru.glob("*.json")):
        return load_mineru_book(slug, base)
    pandoc = root / "pandoc"
    if pandoc.is_dir():
        mds = sorted(pandoc.glob("*.md"))
        if mds:
            return load_pandoc_md(mds[0], slug)
    raise FileNotFoundError(
        f"{slug}: no loadable artifact found (missing {mineru}/*.json or {pandoc}/*.md)"
    )
