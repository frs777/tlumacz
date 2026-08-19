"""Text extraction from binary document formats.

Tłumacz translates documents by feeding plain text (Markdown) to the model.
Binary formats (PDF, DOCX, ODT, EPUB) are first converted to Markdown-style
text here; the translated output is saved as Markdown. Round-tripping back to
the original binary format is out of scope.

Dependencies are optional and detected lazily:

* PDF: the ``pdftotext`` tool (poppler) is preferred; otherwise ``pypdf``.
* DOCX: the ``python-docx`` package (``import docx``); falls back to
  ``pandoc`` (docx -> Markdown) and then LibreOffice when it is missing.
* ODT and EPUB: pure Python standard library (zipfile + XML/HTML parsing).

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

BINARY_FORMATS = frozenset({"pdf", "docx", "odt", "epub"})

_ODF_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


class ExtractionError(Exception):
    """Raised when a binary document cannot be converted to text."""


def is_binary_format(path: str | Path) -> bool:
    """Return whether ``path`` needs text extraction (vs. plain text files)."""
    return Path(path).suffix.lower().lstrip(".") in BINARY_FORMATS


def extract_text(path: str | Path) -> str:
    """Extract Markdown-style text from a binary document.

    Raises :class:`ExtractionError` when the format is unsupported or a
    required optional dependency is missing.
    """
    ext = Path(path).suffix.lower().lstrip(".")
    if ext == "pdf":
        return _extract_pdf(path)
    if ext == "docx":
        return _extract_docx(path)
    if ext == "odt":
        return _extract_odt(path)
    if ext == "epub":
        return _extract_epub(path)
    raise ExtractionError(f"Nieobsługiwany format binarny: .{ext}")


# --------------------------------------------------------------------- PDF --

def _extract_pdf(path: str | Path) -> str:
    binary = shutil.which("pdftotext")
    if binary is not None:
        try:
            result = subprocess.run(
                [binary, "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise ExtractionError(f"pdftotext: {exc}") from exc
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractionError(
            "Ekstrakcja PDF wymaga narzędzia 'pdftotext' (poppler) "
            "albo pakietu pypdf. Zainstaluj któreś z nich."
        ) from exc
    try:
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # noqa: BLE001 - pypdf raises many error types
        raise ExtractionError(f"Nie można odczytać PDF: {exc}") from exc


# ------------------------------------------------------------------- DOCX --

def _extract_docx(path: str | Path) -> str:
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        return _extract_docx_fallback(path)

    try:
        doc = Document(str(path))
        parts: list[str] = []
        for child in doc.element.body.iterchildren():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "p":
                text = Paragraph(child, doc).text.strip()
                if text:
                    parts.append(text)
            elif tag == "tbl":
                table = Table(child, doc)
                rows = [
                    "| " + " | ".join(
                        cell.text.replace("\n", " ").strip() for cell in row.cells
                    ) + " |"
                    for row in table.rows
                ]
                if rows:
                    parts.append("\n".join(rows))
        return "\n\n".join(parts)
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"Nie można odczytać DOCX: {exc}") from exc


def _extract_docx_fallback(path: str | Path) -> str:
    """Fallback DOCX extraction when python-docx is unavailable.

    ``pandoc`` is preferred (fast, reliable docx -> Markdown); LibreOffice is
    used only as a last resort.
    """
    pandoc = shutil.which("pandoc")
    if pandoc is not None:
        try:
            result = subprocess.run(
                [pandoc, str(path), "-t", "markdown"],
                capture_output=True, text=True, check=False,
            )
        except OSError as exc:
            raise ExtractionError(f"pandoc: {exc}") from exc
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        raise ExtractionError(
            "pandoc nie przetworzył DOCX: "
            f"{result.stderr.strip() or result.returncode}"
        )

    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if binary is None:
        raise ExtractionError(
            "Ekstrakcja DOCX wymaga pakietu 'python-docx' "
            "(zainstaluj: pip install python-docx) albo narzędzia pandoc."
        )
    tmpdir = Path(tempfile.mkdtemp(prefix="tlumacz-docx-"))
    try:
        result = subprocess.run(
            [binary, "--headless", "--convert-to", "txt:Text",
             "--outdir", str(tmpdir), str(path)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise ExtractionError(
                "LibreOffice nie przetworzył DOCX: "
                f"{result.stderr.strip() or result.returncode}"
            )
        txt = tmpdir / (Path(path).stem + ".txt")
        if not txt.is_file():
            raise ExtractionError("LibreOffice nie wygenerował tekstu z DOCX.")
        return txt.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ExtractionError(f"LibreOffice: {exc}") from exc
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# -------------------------------------------------------------------- ODT --

def _extract_odt(path: str | Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            content = archive.read("content.xml")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise ExtractionError(f"Nie można otworzyć ODT: {exc}") from exc

    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ExtractionError(f"Nieprawidłowy XML w ODT: {exc}") from exc

    parts: list[str] = []
    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in ("p", "h"):
            text = "".join(elem.itertext()).strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts)


# ------------------------------------------------------------------- EPUB --

class _TextCollector(HTMLParser):
    """Strip HTML, emitting text with newlines after block-level elements."""

    _BLOCK_TAGS = {
        "p",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "br",
        "tr",
        "table",
        "blockquote",
    }

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def text(self) -> str:
        raw = "".join(self._parts)
        return re.sub(r"[ \t]+", " ", raw).strip()


def _extract_epub(path: str | Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            chapters = [
                name
                for name in names
                if name.lower().endswith((".xhtml", ".html", ".htm"))
            ]
            if not chapters:
                raise ExtractionError("W EPUB nie znaleziono plików treści.")
            parts: list[str] = []
            for name in sorted(chapters):
                raw = archive.read(name).decode("utf-8", errors="replace")
                text = _html_to_text(raw)
                if text:
                    parts.append(text)
        return "\n\n".join(parts)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ExtractionError(f"Nie można otworzyć EPUB: {exc}") from exc


def _html_to_text(raw: str) -> str:
    parser = _TextCollector()
    parser.feed(raw)
    parser.close()
    return parser.text()