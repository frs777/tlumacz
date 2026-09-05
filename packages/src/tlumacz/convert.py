"""Convert translated Markdown back to binary document formats.

Round-trip helper: Tłumacz saves translation results as Markdown; this module
converts them back to DOCX, ODT or PDF so users get a translated file in the
original format.

Tools used (detected lazily):

* DOCX: ``npx markdown-docx`` (npm package), falling back to ``pandoc``.
* ODT: ``pandoc``.
* PDF: ``pandoc`` (with an available PDF engine), falling back to
  LibreOffice (convert the ODT to PDF).

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SUPPORTED_FORMATS = frozenset({"docx", "odt", "pdf"})


class ConversionError(Exception):
    """Raised when a Markdown file cannot be converted to another format."""


def convert_markdown(
    input_md: str | Path,
    fmt: str,
    output: str | Path | None = None,
) -> str:
    """Convert ``input_md`` to ``fmt`` and return the output path.

    Raises:
        ConversionError: on unsupported formats, missing input, missing tools
            or a failed conversion.
    """
    fmt = fmt.lower().lstrip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ConversionError(f"Nieobsługiwany format konwersji: .{fmt}")

    src = Path(input_md)
    if not src.is_file():
        raise ConversionError(f"Plik nie istnieje: {src}")

    out = Path(output) if output else src.with_suffix(f".{fmt}")
    out.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "docx":
        return _convert_docx(src, out)
    if fmt == "odt":
        return _convert_odt(src, out)
    return _convert_pdf(src, out)


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise ConversionError(f"{cmd[0]}: {exc}") from exc


def _convert_docx(src: Path, out: Path) -> str:
    pandoc = shutil.which("pandoc")
    if pandoc is not None:
        result = _run([pandoc, str(src), "-o", str(out)])
        if result.returncode == 0 and out.is_file():
            return str(out)

    npx = shutil.which("npx")
    if npx is not None:
        result = _run([npx, "markdown-docx", "-i", str(src), "-o", str(out)])
        if result.returncode == 0 and out.is_file():
            return str(out)

    raise ConversionError(
        "Konwersja do DOCX wymaga pakietu pandoc lub narzędzia npx markdown-docx."
    )


def _convert_odt(src: Path, out: Path) -> str:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ConversionError("Konwersja do ODT wymaga pakietu pandoc.")
    result = _run([pandoc, str(src), "-o", str(out)])
    if result.returncode != 0 or not out.is_file():
        raise ConversionError(
            f"pandoc nie przetworzył ODT: {result.stderr.strip() or result.returncode}"
        )
    return str(out)


def _convert_pdf(src: Path, out: Path) -> str:
    pandoc = shutil.which("pandoc")
    if pandoc is not None:
        result = _run([pandoc, str(src), "-o", str(out)])
        if result.returncode == 0 and out.is_file():
            return str(out)

    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if soffice is None:
        raise ConversionError(
            "Konwersja do PDF wymaga pakietu pandoc (z silnikiem PDF) "
            "albo narzędzia libreoffice."
        )

    odt = out.with_suffix(".odt")
    _convert_odt(src, odt)
    try:
        result = _run(
            [soffice, "--headless", "--convert-to", "pdf",
             "--outdir", str(out.parent), str(odt)]
        )
    finally:
        try:
            odt.unlink()
        except OSError:
            pass
    if result.returncode != 0 or not out.is_file():
        raise ConversionError(
            f"libreoffice nie przetworzył PDF: {result.stderr.strip() or result.returncode}"
        )
    return str(out)
