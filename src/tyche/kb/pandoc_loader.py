"""Parse the Markdown that pandoc produces from docx into a list of Blocks (deterministic).

For docx-sourced classics (here: 星命抉古錄, xingmingjueguilu). docx has no page numbers, so:
- page defaults to 0 (= unpaginated), consistent with the MinerU Block field;
- the body sometimes carries a manual page marker `pNN` (e.g. "五行生旺論 p21"); it is extracted
  as a page hint, carried forward until the next marker, and stripped from the text. It is a
  layout remnant, not an exact page number — a locating hint only.

Block splitting: by blank lines (pandoc's `<table>` blocks from docx have no inner blank lines,
so tables stay intact). Block types (aligned with MinerU's text/title/table):
- `<table>…` / `<col…` / `|…` (HTML or pipe table) -> "table" (kept verbatim, cells not parsed)
- a whole block wrapped in `**…**`, or an ATX `#` heading (pandoc's docx-heading output) -> "title"
- otherwise -> "text"

Note: loading is faithful and does not drop the table of contents (this book repeats it up front);
whether to drop it is a decision for the triage stage.
"""

import re
from pathlib import Path
from typing import Union

from .blocks import Block

# Treat only a standalone-token pNN as a page marker (avoid URLs / percentages / in-word alnum).
_PAGE_RE = re.compile(r"(?<![A-Za-z0-9])p(\d{1,3})(?![A-Za-z0-9])")
_BOLD_RE = re.compile(r"^\*\*(.+)\*\*$", re.S)
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")   # [text](url) -> text
_UTAG_RE = re.compile(r"</?u>")


def _split_blocks(text: str) -> list[str]:
    """Split into raw blocks by blank lines, keeping intra-block newlines."""
    blocks: list[str] = []
    cur: list[str] = []
    for line in text.splitlines():
        if line.strip() == "":
            if cur:
                blocks.append("\n".join(cur))
                cur = []
        else:
            cur.append(line.rstrip())
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def _is_table(block: str) -> bool:
    s = block.lstrip()
    return s.startswith("<table") or s.startswith("<col") or s.startswith("|")


def _clean_inline(s: str) -> str:
    s = _LINK_RE.sub(r"\1", s)
    s = _UTAG_RE.sub("", s)
    return s


def _strip_page_markers(s: str) -> str:
    return _PAGE_RE.sub("", s).replace("  ", " ").strip()


def _classify(block: str) -> tuple[str, str]:
    """Return (type, text). Tables verbatim; titles unwrapped; body joins soft wraps (no spaces for CJK)."""
    if _is_table(block):
        return "table", block.strip()
    joined = "".join(l.strip() for l in block.splitlines())
    if joined.startswith("#"):
        return "title", _clean_inline(joined.lstrip("# ").strip())
    m = _BOLD_RE.match(joined)
    if m and "**" not in m.group(1):
        return "title", _clean_inline(m.group(1).strip())
    return "text", _clean_inline(joined)


def load_pandoc_md(path: Union[str, Path], book: str) -> list[Block]:
    text = Path(path).read_text(encoding="utf-8")
    out: list[Block] = []
    page = 0
    for i, raw in enumerate(_split_blocks(text)):
        typ, body = _classify(raw)
        marks = _PAGE_RE.findall(raw)
        if marks and typ != "table":
            page = int(marks[-1])
            body = _strip_page_markers(body)
        body = body.strip()
        if body:
            out.append(Block(book=book, page=page, type=typ, index=i, text=body))
    return out
