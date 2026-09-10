"""Glossary support for Tłumacz.

A glossary maps source terms or phrases to fixed translations. Entries are
stored in a two-column CSV file (``source,target``) so they can be edited in
any spreadsheet application or from the GUI. The glossary is injected into
the translation system prompt, telling the model to use the fixed
translations instead of inventing its own.

The parser is robust to the two most common layouts:

* ``source,target`` with an optional header row (``source,target`` or
  ``Pattern,Substitution`` — headers are detected and skipped);
* targets prefixed with ``#`` (as produced by inflection/morphology
  dictionaries), e.g. ``Aarona,#Aaron`` — the prefix is stripped.

To keep prompts sane, only a limited number of entries is injected and
identity pairs (``term -> same term``) are skipped, since they add no
information for the model.

This module is intentionally free of Qt/CLI dependencies so it can be reused
by the GUI and any future CLI.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Iterable, Optional

# A row whose first cell matches one of these labels is treated as a header
# row and skipped. This lets spreadsheets (which often start with
# ``source,target``) be used directly as glossary files.
_SOURCE_HEADERS = {
    "source",
    "src",
    "key",
    "from",
    "orig",
    "original",
    "zrodlo",
    "źródło",
    "klucz",
    "termin",
    "pattern",
    "wzor",
    "wzór",
}
_TARGET_HEADERS = {
    "target",
    "translation",
    "dest",
    "to",
    "tłumaczenie",
    "tlumaczenie",
    "value",
    "wartość",
    "wartosc",
    "substitution",
    "zamiana",
    "zastapienie",
    "zastąpienie",
}

MAX_PROMPT_ENTRIES = 300


@dataclass
class Glossary:
    """An ordered collection of ``(source, target)`` translation pairs."""

    entries: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_csv(
        cls,
        path: str | os.PathLike,
        max_entries: Optional[int] = None,
    ) -> "Glossary":
        """Load entries from a two-column CSV file.

        An optional header row is skipped, a leading ``#`` on the target is
        stripped, and entries are deduplicated by source (case-insensitive;
        the last occurrence wins). Malformed rows (fewer than two non-empty
        cells) are ignored. Reading stops early once ``max_entries`` entries
        have been collected (useful for very large dictionaries).

        Raises:
            OSError: If the file cannot be read.
        """
        glossary = cls()
        seen: set[str] = set()
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if max_entries is not None and len(glossary.entries) >= max_entries:
                    break
                source, target = _normalize_row(row)
                if source is None or target is None or _is_header(source, target):
                    continue
                target = target[1:] if target.startswith("#") else target
                target = target.strip()
                if not target:
                    continue
                key = source.casefold()
                if key in seen:
                    continue
                seen.add(key)
                glossary.entries.append((source, target))
        return glossary

    def add(self, source: str, target: str) -> bool:
        """Add a ``(source, target)`` pair if it is not already present.

        Returns ``False`` when the entry is empty or already exists
        (case-insensitive comparison on the source term).
        """
        source = source.strip()
        target = target.strip()
        if not source or not target:
            return False
        for existing_source, _ in self.entries:
            if existing_source.casefold() == source.casefold():
                return False
        self.entries.append((source, target))
        return True

    def save(self, path: str | os.PathLike) -> None:
        """Write all entries to ``path`` as a CSV with a header row."""
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target"])
            writer.writerows(self.entries)

    def to_prompt(self, max_entries: int = MAX_PROMPT_ENTRIES) -> str:
        """Return a prompt fragment listing the glossary entries.

        Identity pairs (``term -> same term``) are skipped because they carry
        no instruction for the model. Returns an empty string when nothing
        remains to include.
        """
        pairs = [
            (source, target)
            for source, target in self.entries
            if source.casefold() != target.casefold()
        ][:max_entries]
        if not pairs:
            return ""
        lines = [f"- {source} => {target}" for source, target in pairs]
        return (
            "Use the following glossary terms exactly, do not translate them "
            "differently:\n" + "\n".join(lines)
        )

    def __len__(self) -> int:
        return len(self.entries)


def _normalize_row(row: Iterable[str]) -> tuple[str | None, str | None]:
    """Return stripped source/target cells, or ``None`` for missing ones."""
    cells = [c.strip() for c in row]
    if len(cells) < 2 or not cells[0] or not cells[1]:
        return None, None
    return cells[0], cells[1]


def _is_header(source: str, target: str) -> bool:
    return (
        source.casefold() in _SOURCE_HEADERS
        and target.casefold() in _TARGET_HEADERS
    )