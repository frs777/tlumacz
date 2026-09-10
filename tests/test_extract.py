"""Tests for binary document structure extraction and reconstruction."""

import zipfile

import pytest

from tlumacz.extract import (
    ExtractionError,
    extract_epub_structure,
    is_binary_format,
    reconstruct_epub,
)


def test_is_binary_format():
    assert is_binary_format("x.pdf")
    assert is_binary_format("a/b.DOCX")
    assert is_binary_format("book.epub")
    assert is_binary_format("doc.odt")
    assert not is_binary_format("x.md")
    assert not is_binary_format("x.txt")


def test_extract_epub_structure_spine_order(tmp_path):
    html_b = "<html><body><p>B</p></body></html>"
    html_a = "<html><body><p>A</p></body></html>"
    opf = (
        '<?xml version="1.0"?>'
        '<package xmlns="http://www.idpf.org/2007/opf">'
        '<manifest>'
        '<item id="c1" href="b.xhtml" media-type="application/xhtml+xml"/>'
        '<item id="c0" href="a.xhtml" media-type="application/xhtml+xml"/>'
        '<item id="img" href="c.png" media-type="image/png"/>'
        '</manifest>'
        '<spine><itemref idref="c0"/><itemref idref="c1"/></spine>'
        '</package>'
    )
    container = (
        '<?xml version="1.0"?>'
        '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles>'
        '</container>'
    )
    buf = __import__("io").BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/a.xhtml", html_a)
        z.writestr("OEBPS/b.xhtml", html_b)
        z.writestr("OEBPS/c.png", b"png")
    path = tmp_path / "book.epub"
    path.write_bytes(buf.getvalue())

    structure = extract_epub_structure(path)
    assert structure["xhtml_paths"] == ["OEBPS/a.xhtml", "OEBPS/b.xhtml"]
    assert structure["files"]["OEBPS/c.png"] == b"png"
    assert structure["files"]["mimetype"] == b"application/epub+zip"


def test_reconstruct_epub_mimetype_first_stored(tmp_path):
    files = {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": b"<container/>",
        "OEBPS/content.xhtml": b"<html><body>STARY</body></html>",
        "OEBPS/cover.png": b"\x89PNG",
    }
    out = tmp_path / "out.epub"
    reconstruct_epub(
        files,
        {"OEBPS/content.xhtml": "<html><body>NOWY</body></html>".encode("utf-8")},
        out,
    )
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert names[0] == "mimetype"
        assert z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert z.read("OEBPS/content.xhtml") == b"<html><body>NOWY</body></html>"
        assert z.read("OEBPS/cover.png") == b"\x89PNG"