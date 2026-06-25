"""Parse MinerU's `pdf_info` JSON into a list of Blocks (deterministic).

MinerU JSON: top-level dict -> `pdf_info` (one element per page) -> `para_blocks` (body blocks).
Each block: `type` (text/title/table...), `index` (page-local reading order), `bbox`,
`lines[].spans[].content`. `discarded_blocks` (headers/footers) are ignored.

Split-book page restoration: when the filename contains `_p{start}-{end}`, the source page
= page_idx + 1 + (start - 1). For a single file (no `_p`), it is page_idx + 1.
"""

import json
import re
from pathlib import Path
from typing import Union

from .blocks import Block

_PART_RE = re.compile(r"_p(\d+)-(\d+)")


def _collect_content(obj) -> list[str]:
    """Recursively collect every span's content (in order ≈ reading order); stable for text/title/table."""
    parts: list[str] = []
    if isinstance(obj, dict):
        c = obj.get("content")
        if isinstance(c, str):
            parts.append(c)
        for k, v in obj.items():
            if k == "content":
                continue
            parts.extend(_collect_content(v))
    elif isinstance(obj, list):
        for x in obj:
            parts.extend(_collect_content(x))
    return parts


def _block_text(block: dict) -> str:
    return "".join(_collect_content(block)).strip()


def part_offset(stem: str) -> int:
    """Parse the source start-page offset (start - 1) from a filename stem. 0 if no `_p`."""
    m = _PART_RE.search(stem)
    return int(m.group(1)) - 1 if m else 0


def load_mineru_json(path: Union[str, Path], book: str, page_offset: int = 0) -> list[Block]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    blocks: list[Block] = []
    for pg in data.get("pdf_info", []):
        page = pg.get("page_idx", 0) + 1 + page_offset
        for b in pg.get("para_blocks", []):
            text = _block_text(b)
            if text:
                blocks.append(Block(book=book, page=page, type=b.get("type", ""),
                                    index=b.get("index", 0), text=text))
    return blocks


def load_mineru_book(slug: str, base: Union[str, Path] = "docs_local") -> list[Block]:
    """Load all MinerU parts of a book, merged by split-page offset (continuous source pages)."""
    mineru_dir = Path(base) / slug / "mineru"
    blocks: list[Block] = []
    for f in sorted(mineru_dir.glob("*.json")):
        blocks.extend(load_mineru_json(f, slug, page_offset=part_offset(f.stem)))
    return blocks
