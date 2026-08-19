"""Skill discovery and injection for Tłumacz.

A skill is a short Markdown instruction file bundled in the
``tlumacz/skills/`` package. Each skill targets one or more input file
formats; when the skill is enabled in the GUI and the input file's extension
matches, its instructions are appended to the translation system prompt.

Skill file layout::

    ---
    name: Markdown
    formats: md, markdown
    ---
    <instructions for the model>

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class Skill:
    """A bundled translation skill for one or more file formats."""

    name: str
    formats: tuple[str, ...]
    text: str

    def matches(self, path: str | Path) -> bool:
        ext = Path(path).suffix.lower().lstrip(".")
        return ext in self.formats


def discover_skills() -> list[Skill]:
    """Return the bundled skills, sorted by name for a stable order."""
    skills: list[Skill] = []
    try:
        entries = resources.files("tlumacz.skills").iterdir()
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        return skills
    for entry in entries:
        if entry.name.lower().endswith(".md"):
            try:
                text = entry.read_text(encoding="utf-8")
            except OSError:
                continue
            skill = _parse_skill(entry.name, text)
            if skill is not None:
                skills.append(skill)
    return sorted(skills, key=lambda s: s.name.casefold())


def text_for_file(
    path: str | Path, enabled: Iterable[str] = ()
) -> tuple[str, str]:
    """Return ``(skill_text, skill_name)`` for ``path``.

    Returns ``("", "")`` when no enabled skill matches the file extension.
    """
    enabled = set(enabled)
    for skill in discover_skills():
        if skill.name in enabled and skill.matches(path):
            return skill.text, skill.name
    return "", ""


def _parse_skill(filename: str, text: str) -> Optional[Skill]:
    """Parse a skill file with optional ``---`` frontmatter."""
    meta: dict[str, str] = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) < 3:
            return None
        for line in parts[1].strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip().lower()] = value.strip()
        body = parts[2]
    else:
        body = text

    name = meta.get("name")
    formats_raw = meta.get("formats")
    if not name or not formats_raw:
        return None
    formats = tuple(
        fmt.strip().lower()
        for fmt in formats_raw.split(",")
        if fmt.strip()
    )
    if not formats or not body.strip():
        return None
    return Skill(name=name, formats=formats, text=body.strip())