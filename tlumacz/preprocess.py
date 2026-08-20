"""Preprocessing for faster, higher-quality translation.

Three transformations applied before text reaches the model:

* **Protection** — fenced/inline code and URLs are replaced by short
  placeholders so the model cannot reword them; the originals are restored
  afterwards. This keeps technical content verbatim and shrinks the output.
* **Line filtering** — lines matching ``skip_patterns`` (YAML metadata such
  as ``license:``, ``author:``, ``version:``) never reach the model and are
  copied to the output unchanged.
* **Section-aware chunking** — text is split into chunks at Markdown heading
  or paragraph boundaries so whole sections are translated together instead
  of being cut mid-table.

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable

# --- Protection ------------------------------------------------------------

_PLACEHOLDER = "⟦PROT_{0}⟧"
_PLACEHOLDER_RE = re.compile(r"⟦PROT_(\d+)⟧")

_PROTECT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("fenced", re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)),
    ("inline", re.compile(r"`[^`\n]+`")),
    ("tag", re.compile(r"<[^>]*>")),
    ("url", re.compile(r"https?://[^\s<>()]+")),
]


def protect(text: str) -> tuple[str, list[str]]:
    """Mask protected regions with placeholders.

    Returns ``(masked_text, originals)`` where ``originals[i]`` is the text
    that ``⟦PROT_i⟧`` stands for.
    """
    originals: list[str] = []
    masked = text
    for _, pattern in _PROTECT_PATTERNS:
        masked = pattern.sub(_replace_protected(originals), masked)
    return masked, originals


def _replace_protected(originals: list[str]) -> Callable[[re.Match[str]], str]:
    def _sub(match: re.Match[str]) -> str:
        originals.append(match.group(0))
        return _PLACEHOLDER.format(len(originals) - 1)
    return _sub


def restore(text: str, originals: Iterable[str]) -> str:
    """Replace placeholders in ``text`` with the original protected content.

    Placeholders the model mangled or dropped are left untouched.
    """
    originals = list(originals)

    def _sub(match: re.Match[str]) -> str:
        index = int(match.group(1))
        if 0 <= index < len(originals):
            return originals[index]
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_sub, text)


# --- Line filtering --------------------------------------------------------

DEFAULT_SKIP_PATTERNS: list[str] = [
    r"^\s*---\s*$",
    r"^\s*(name|license|author|metadata|version|tags|created|updated)\s*:",
]


def compile_skip_patterns(patterns: Iterable[str]) -> list[re.Pattern[str]]:
    """Compile skip patterns, ignoring invalid regexes."""
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error:
            continue
    return compiled


def is_skipped(line: str, compiled: Iterable[re.Pattern[str]]) -> bool:
    """Return ``True`` when ``line`` matches any skip pattern."""
    return any(p.search(line) for p in compiled)


# --- Section-aware chunking ------------------------------------------------

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")


_PLACEHOLDER_SPLIT_RE = re.compile(r"(⟦PROT_\d+⟧)")


def split_xml_segments(
    text: str,
    chunk_size: int,
) -> list[tuple[str, str]]:
    """Split XML/HTML text into translate segments without breaking placeholders.

    Tag-protected regions (``⟦PROT_n⟧``) are atomic tokens: they are never cut
    in half, so ``restore()`` can always put the original tags back. Plain text
    runs are cut at ``chunk_size`` characters when needed. Returns a list of
    ``("translate", content)`` tuples (XML is translated as a whole; there are
    no ``keep`` lines).
    """
    tokens = _PLACEHOLDER_SPLIT_RE.split(text)
    segments: list[tuple[str, str]] = []
    current = ""

    for token in tokens:
        if not token:
            continue
        if len(token) > chunk_size:
            if current:
                segments.append(("translate", current))
                current = ""
            for i in range(0, len(token), chunk_size):
                segments.append(("translate", token[i : i + chunk_size]))
            continue
        if current and len(current) + len(token) > chunk_size:
            segments.append(("translate", current))
            current = ""
        current += token

    if current:
        segments.append(("translate", current))
    return segments


def split_segments(
    text: str,
    chunk_size: int,
    skip_patterns: Iterable[str] = (),
) -> list[tuple[str, str]]:
    """Split ``text`` into ordered ``("keep" | "translate", content)`` segments.

    ``keep`` segments are lines matching a skip pattern and are copied to the
    output verbatim. ``translate`` segments are section-aligned blocks
    (headings and paragraphs) that never exceed ``chunk_size`` characters.
    """
    skip = compile_skip_patterns(skip_patterns)
    lines = text.splitlines()
    segments: list[tuple[str, str]] = []
    pending: list[str] = []
    pending_len = 0

    def flush() -> None:
        nonlocal pending, pending_len
        if pending:
            if "\n".join(pending).strip():
                segments.append(("translate", "\n".join(pending)))
            else:
                segments.append(("keep", "\n".join(pending)))
            pending = []
            pending_len = 0

    for line in lines:
        if is_skipped(line, skip):
            flush()
            segments.append(("keep", line))
            continue
        line_len = len(line)
        if line_len > chunk_size:
            flush()
            for i in range(0, line_len, chunk_size):
                segments.append(("translate", line[i : i + chunk_size]))
            continue
        is_heading = bool(_HEADING_RE.match(line))
        if pending and pending_len + line_len + 1 > chunk_size:
            flush()
        elif pending and is_heading and pending_len >= chunk_size * 0.6:
            flush()
        pending.append(line)
        pending_len += line_len + 1

    flush()
    return segments