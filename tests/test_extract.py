"""Tests for binary document text extraction."""

import subprocess
import zipfile

import pytest

from tlumacz.extract import (
    ExtractionError,
    extract_text,
    is_binary_format,
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