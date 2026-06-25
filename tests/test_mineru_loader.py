"""MinerU loader tests (use the small in-repo fixture; no dependency on docs_local)."""

from pathlib import Path

from tyche.kb import load_mineru_json, part_offset

FIXTURE = Path(__file__).parent / "fixtures" / "mineru_sample.json"


def test_parse_blocks_and_pages():
    blocks = load_mineru_json(FIXTURE, "testbook")
    # 3 body blocks (title + text @p1, text @p2); the header (discarded) is skipped
    assert len(blocks) == 3
    assert [b.type for b in blocks] == ["title", "text", "text"]
    assert [b.page for b in blocks] == [1, 1, 2]            # page_idx + 1
    assert blocks[0].text == "论财官"
    assert blocks[1].text == "日主旺，财官有气则富贵。"     # multi-span join
    assert blocks[2].text == "伤官见官，为祸百端。"
    assert all(b.book == "testbook" for b in blocks)
    # the header must not leak in
    assert all("页眉" not in b.text for b in blocks)


def test_page_offset_split_books():
    # second part of a split book: start=149 -> offset 148 -> page_idx 0 restores to source page 149
    blocks = load_mineru_json(FIXTURE, "b", page_offset=148)
    assert blocks[0].page == 149
    assert blocks[2].page == 150


def test_part_offset_parsing():
    assert part_offset("sanmingtonghui_p149-295") == 148
    assert part_offset("sanmingtonghui_p001-148") == 0
    assert part_offset("yujingaojue") == 0
    assert part_offset("minglijinghua") == 0
