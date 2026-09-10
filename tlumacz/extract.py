"""Text extraction and reconstruction for binary document formats.

Tłumacz translates binary formats (PDF, DOCX, ODT, EPUB) using round-trip
structure extraction — the original format is preserved 1:1. Text is extracted
with positions (PDF via PyMuPDF) or XML structure (DOCX/ODT/EPUB), translated,
and reconstructed back into the original archive.

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

BINARY_FORMATS = frozenset({"pdf", "docx", "odt", "epub"})


class ExtractionError(Exception):
    """Raised when a binary document cannot be processed."""


def is_binary_format(path: str | Path) -> bool:
    """Return whether ``path`` is a binary format handled by round-trip translation."""
    return Path(path).suffix.lower().lstrip(".") in BINARY_FORMATS


# ---------------------------------------------------------------------------
# EPUB structure extraction and reconstruction (bez konwersji na Markdown)
# ---------------------------------------------------------------------------

_XHTML_SUFFIXES = (".xhtml", ".html", ".htm")


def extract_epub_structure(path: str | Path) -> dict:
    """Extract the raw content of an EPUB as a mapping of relative paths to bytes.

    All files (XHTML, CSS, images, fonts, mimetype, META-INF, OPF, NCX) are
    preserved verbatim. ``xhtml_paths`` lists the content files in their
    logical reading order (derived from the OPF spine, falling back to a
    sorted name order).

    Returns:
        dict with ``files`` (rel_path -> bytes) and ``xhtml_paths`` (list[str]).
    """
    try:
        with zipfile.ZipFile(path) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
    except (OSError, zipfile.BadZipFile) as exc:
        raise ExtractionError(f"Nie można otworzyć EPUB: {exc}") from exc

    xhtml = [name for name in files if _is_xhtml(name)]
    if not xhtml:
        raise ExtractionError("W EPUB nie znaleziono plików treści.")

    return {"files": files, "xhtml_paths": _epub_reading_order(files)}


def _is_xhtml(name: str) -> bool:
    return name.lower().endswith(_XHTML_SUFFIXES)


def _epub_reading_order(files: dict[str, bytes]) -> list[str]:
    """Return XHTML paths in OPF spine order; fall back to sorted names."""
    xhtml = [name for name in files if _is_xhtml(name)]

    def _resolve(opf_dir: str, href: str) -> str:
        href = href.split("#", 1)[0]
        from urllib.parse import unquote
        href = unquote(href)
        return f"{opf_dir}/{href}" if opf_dir else href

    try:
        container = ElementTree.fromstring(files["META-INF/container.xml"])
        ns_c = "{urn:oasis:names:tc:opendocument:xmlns:container}"
        rootfile = container.find(f".//{ns_c}rootfile")
        if rootfile is None:
            raise KeyError("rootfile")
        opf_path = rootfile.get("full-path", "content.opf")
        opf = ElementTree.fromstring(files[opf_path])
        ns = "{http://www.idpf.org/2007/opf}"
        manifest = {
            item.get("id"): item.get("href")
            for item in opf.findall(f".//{ns}manifest/{ns}item")
        }
        opf_dir = opf_path.rsplit("/", 1)[0] if "/" in opf_path else ""
        order: list[str] = []
        for ref in opf.findall(f".//{ns}spine/{ns}itemref"):
            href = manifest.get(ref.get("idref"))
            if href is None:
                continue
            rel = _resolve(opf_dir, href)
            if rel in files and _is_xhtml(rel) and rel not in order:
                order.append(rel)
        if order:
            remaining = sorted(name for name in xhtml if name not in order)
            return order + remaining
    except Exception:  # noqa: BLE001 - malformed OPF; fall back to sorted names
        pass
    return sorted(xhtml)


def reconstruct_epub(
    files: dict[str, bytes],
    updates: dict[str, bytes],
    output_path: str | Path,
) -> None:
    """Rebuild an EPUB from its raw files plus translated XHTML content.

    Args:
        files: rel_path -> bytes, as returned by :func:`extract_epub_structure`.
        updates: rel_path -> bytes to overwrite in ``files`` (translated XHTML).
        output_path: destination ``.epub`` path.
    """
    merged = dict(files)
    merged.update(updates)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        if "mimetype" in merged:
            zout.writestr(
                "mimetype", merged.pop("mimetype"), compress_type=zipfile.ZIP_STORED
            )
        for name in sorted(n for n in merged if n.startswith("META-INF/")):
            zout.writestr(name, merged.pop(name))
        for name, data in merged.items():
            zout.writestr(name, data)


# --------------------------------------------------------------- OFFICE (ODF/DOCX) --

_DOCX_CONTENT_FILES = {
    "word/document.xml",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
}


def _is_docx_content(name: str) -> bool:
    if name in _DOCX_CONTENT_FILES:
        return True
    base = name.rsplit("/", 1)[-1]
    return base.startswith(("header", "footer")) and name.endswith(".xml")


def extract_office_structure(path: str | Path, ext: str) -> dict:
    """Extract the raw content of a DOCX/ODT archive for in-place translation.

    Returns:
        dict with ``files`` (rel_path -> bytes) and ``content_paths`` (list of
        XML files whose text should be translated; the rest is copied verbatim).
    """
    label = "ODT" if ext == "odt" else "DOCX"
    try:
        with zipfile.ZipFile(path) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
    except (OSError, zipfile.BadZipFile) as exc:
        raise ExtractionError(f"Nie można otworzyć {label}: {exc}") from exc

    if ext == "odt":
        content_paths = [name for name in files if name == "content.xml"]
    else:
        content_paths = sorted(name for name in files if _is_docx_content(name))

    if not content_paths:
        raise ExtractionError(
            f"W pliku {label} nie znaleziono plików treści do przetłumaczenia."
        )
    return {"files": files, "content_paths": content_paths}


def reconstruct_zip(
    files: dict[str, bytes],
    updates: dict[str, bytes],
    output_path: str | Path,
) -> None:
    """Rebuild a ZIP-based document (DOCX/ODT) from raw files plus updates.

    Zachowuje oryginalną kolejność plików z archiwum — ważne dla DOCX/ODT
    które wymagają specyficznej kolejności (np. [Content_Types].xml na początku).

    Args:
        files: rel_path -> bytes, as returned by :func:`extract_office_structure`.
        updates: rel_path -> bytes to overwrite in ``files`` (translated XML).
        output_path: destination document path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        # Iteruj po oryginalnej kolejności plików z archiwum
        for name in files:
            data = updates.get(name, files[name])
            zout.writestr(name, data)