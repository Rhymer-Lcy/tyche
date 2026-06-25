"""pandoc (docx->md) loader + unified load_book dispatch (in-repo fixture; no docs_local)."""

from pathlib import Path

import pytest

from tyche.kb import load_pandoc_md, load_book

FIXTURE = Path(__file__).parent / "fixtures" / "pandoc_sample.md"


def test_types_and_text():
    blocks = load_pandoc_md(FIXTURE, "testbook")
    types = [b.type for b in blocks]
    # title table, 序 (text), the annotation (text), 卷一 (title), 貴人論 (title),
    # discussion (text), numbered item (text), verse (text), 五行旺相表 (title), html table
    assert types == ["table", "text", "text", "title", "title",
                     "text", "text", "text", "title", "table"]
    assert all(b.book == "testbook" for b in blocks)


def test_title_unwrapped_and_page_stripped():
    blocks = load_pandoc_md(FIXTURE, "b")
    titles = {b.text: b for b in blocks if b.type == "title"}
    assert "卷一" in titles               # ** unwrapped + " p21" marker stripped
    assert "p21" not in titles["卷一"].text
    assert "五行旺相表" in titles


def test_page_carry_forward():
    blocks = load_pandoc_md(FIXTURE, "b")
    by_text = {b.text: b.page for b in blocks}
    assert by_text["卷一"] == 21          # page marker hit
    assert by_text["貴人論"] == 21         # carried forward, no new marker yet
    assert by_text["五行旺相表"] == 22     # new marker updates it


def test_inline_cleanup():
    blocks = load_pandoc_md(FIXTURE, "b")
    xu = next(b for b in blocks if b.text.startswith("北魏"))
    assert "原書" in xu.text               # link text kept
    assert "http" not in xu.text and "<u>" not in xu.text  # url / tags stripped


def test_soft_wrap_merged():
    blocks = load_pandoc_md(FIXTURE, "b")
    lun = next(b for b in blocks if b.text.startswith("貴人之名"))
    # soft wraps within a block merge into one line, no spaces inserted between CJK
    assert lun.text == "貴人之名甚多，其可信用者惟天乙耳。貴人不在生旺之地。"


def test_load_book_dispatch_pandoc(tmp_path):
    root = tmp_path / "mybook" / "pandoc"
    root.mkdir(parents=True)
    (root / "mybook.md").write_text("**Title**\n\nA paragraph.\n", encoding="utf-8")
    blocks = load_book("mybook", base=tmp_path)
    assert [b.type for b in blocks] == ["title", "text"]
    assert blocks[0].text == "Title"


def test_load_book_missing_raises(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(FileNotFoundError):
        load_book("empty", base=tmp_path)
