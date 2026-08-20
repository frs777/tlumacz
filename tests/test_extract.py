"""Tests for binary document text extraction."""

import subprocess
import zipfile

import pytest

from tlumacz.extract import (
    ExtractionError,
    extract_epub_structure,
    extract_text,
    is_binary_format,
    reconstruct_epub,
)


def _odt_bytes() -> bytes:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body><office:text>
    <text:h>Nagłówek</text:h>
    <text:p>Akapit pierwszy.</text:p>
    <text:p>Akapit <text:span>drugi</text:span>.</text:p>
  </office:text></office:body>
</office:document-content>
"""
    buf = __import__("io").BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("content.xml", xml)
    return buf.getvalue()


def _epub_bytes() -> bytes:
    html = (
        "<html><head><title>x</title></head><body>"
        "<h1>Rozdział 1</h1><p>To jest <b>tekst</b>.<br>Nowa linia.</p>"
        "</body></html>"
    )
    buf = __import__("io").BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("OEBPS/content.xhtml", html)
    return buf.getvalue()


def test_is_binary_format():
    assert is_binary_format("x.pdf")
    assert is_binary_format("a/b.DOCX")
    assert is_binary_format("book.epub")
    assert is_binary_format("doc.odt")
    assert not is_binary_format("x.md")
    assert not is_binary_format("x.txt")


def test_extract_odt(tmp_path):
    path = tmp_path / "doc.odt"
    path.write_bytes(_odt_bytes())
    text = extract_text(path)
    assert "Nagłówek" in text
    assert "Akapit pierwszy." in text
    assert "Akapit drugi." in text


def test_extract_epub(tmp_path):
    path = tmp_path / "book.epub"
    path.write_bytes(_epub_bytes())
    text = extract_text(path)
    assert "Rozdział 1" in text
    assert "To jest tekst." in text
    assert "Nowa linia." in text


def test_extract_unsupported_format(tmp_path):
    path = tmp_path / "x.xyz"
    path.write_text("coś", encoding="utf-8")
    with pytest.raises(ExtractionError):
        extract_text(path)


def test_extract_pdf_missing_deps(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "tlumacz.extract.shutil.which", lambda _name: None
    )
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"%PDF-not-really")
    with pytest.raises(ExtractionError, match="PDF"):
        extract_text(path)


def test_extract_docx_missing_deps(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "tlumacz.extract.shutil.which", lambda _name: None
    )
    path = tmp_path / "bad.docx"
    path.write_bytes(b"PK\x03\x04not-a-docx")
    with pytest.raises(ExtractionError, match="python-docx"):
        extract_text(path)


def test_extract_docx_pandoc_fallback(tmp_path, monkeypatch):
    from tlumacz.extract import _extract_docx_fallback

    fake = tmp_path / "fake-pandoc"

    def _fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(
            cmd, 0, stdout="# Nagłówek\n\nTreść akapitu.\n"
        )

    monkeypatch.setattr("tlumacz.extract.shutil.which", lambda _name: str(fake))
    monkeypatch.setattr("tlumacz.extract.subprocess.run", _fake_run)
    path = tmp_path / "doc.docx"
    path.write_bytes(b"PK\x03\x04fake")
    assert _extract_docx_fallback(path) == "# Nagłówek\n\nTreść akapitu."


def test_extract_odt_corrupt_zip(tmp_path):
    path = tmp_path / "bad.odt"
    path.write_bytes(b"not a zip at all")
    with pytest.raises(ExtractionError):
        extract_text(path)


def test_extract_epub_missing_content(tmp_path):
    buf = __import__("io").BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
    path = tmp_path / "empty.epub"
    path.write_bytes(buf.getvalue())
    with pytest.raises(ExtractionError, match="EPUB"):
        extract_text(path)


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