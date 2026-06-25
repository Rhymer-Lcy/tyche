"""The knowledge base's minimal text unit: Block (a deterministic load result, source-agnostic).

Both loaders (MinerU for PDF, pandoc for docx) emit the same Block, so downstream stages
(triage / chunk / retrieval) face only this one structure.

Fields:
- book   book slug
- page   page number in the source book (1-based). 0 means unpaginated (docx has no page
         numbers, or the page marker is missing).
- type   text / title / table / image / ... (both loaders align to this vocabulary)
- index  reading order (page-local for MinerU; whole-document for pandoc)
- text   the block's text
"""

from dataclasses import dataclass


@dataclass
class Block:
    book: str
    page: int
    type: str
    index: int
    text: str
