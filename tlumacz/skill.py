"""Skill discovery and injection for Tłumacz.

A skill is a short Markdown instruction file with ``name``/``formats``
frontmatter, e.g.::

    ---
    name: Markdown
    formats: md, markdown
    ---
    <instructions for the model>

Skills come from two places, merged by name (a user skill overrides a
bundled one with the same name):

* bundled with the app in the ``tlumacz/skills/`` package;
* user-defined in ``<config_dir>/skills/`` (e.g.
  ``~/.config/tlumacz/skills/``), which is created lazily on first save.

When the skill is enabled in the GUI and the input file's extension matches,
its instructions are appended to the translation system prompt.

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Optional

from .qt_gui.config import config_dir

_FRONTMATTER_RE = re.compile(
    r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)(.*)$",
    re.DOTALL,
)


@dataclass
class Skill:
    """A bundled translation skill for one or more file formats."""

    name: str
    formats: tuple[str, ...]
    text: str
    skip_patterns: tuple[str, ...] = ()

    def matches(self, path: str | Path) -> bool:
        ext = Path(path).suffix.lower().lstrip(".")
        return ext in self.formats


_SKILL_TEMPLATE_NAME = "SKILL_TEMPLATE.md"


def discover_skills() -> list[Skill]:
    """Return the bundled and user skills, sorted by name for a stable order.

    User skills from ``<config_dir>/skills/`` win over bundled ones with the
    same name.
    """
    by_name: dict[str, Skill] = {}

    def collect(entries: Iterable[Path]) -> None:
        for entry in entries:
            if entry.name.lower().endswith(".md") and entry.name != _SKILL_TEMPLATE_NAME:
                try:
                    text = entry.read_text(encoding="utf-8")
                except OSError:
                    continue
                skill = _parse_skill(entry.name, text)
                if skill is not None:
                    by_name[skill.name] = skill

    try:
        collect(resources.files("tlumacz.skills").iterdir())
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass

    user_dir = user_skills_dir()
    if user_dir.is_dir():
        collect(user_dir.iterdir())

    return sorted(by_name.values(), key=lambda s: s.name.casefold())


def user_skills_dir() -> Path:
    """Return the user skills directory (created lazily by :func:`save_skill`)."""
    return config_dir() / "skills"


def save_skill(
    path: str | Path,
    name: str,
    formats: str,
    text: str,
    skip_patterns: str = "",
) -> Path:
    """Write a user skill file into the user skills directory.

    The filename is derived from the skill name (lowercased, non-alphanumeric
    characters replaced with ``-``). ``skip_patterns`` is an optional
    comma-separated list of regexes written into the frontmatter. Returns the
    created path.
    """
    target = user_skills_dir() / _slugify(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = f"name: {name}\nformats: {formats}\n"
    if skip_patterns.strip():
        frontmatter += f"skip_patterns: {skip_patterns.strip()}\n"
    target.write_text(
        f"---\n{frontmatter}---\n\n{text.strip()}\n",
        encoding="utf-8",
    )
    return target


def _slugify(name: str) -> str:
    safe = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return (safe or "skill") + ".md"


def parse_skill(filename: str, text: str) -> Optional[Skill]:
    """Public wrapper around :func:`_parse_skill` for the GUI."""
    return _parse_skill(filename, text)


def text_for_file(
    path: str | Path, enabled: Iterable[str] = ()
) -> tuple[str, str, tuple[str, ...]]:
    """Return ``(skill_text, skill_name, skip_patterns)`` for ``path``.

    Returns ``("", "", ())`` when no enabled skill matches the file extension.
    """
    enabled = set(enabled)
    for skill in discover_skills():
        if skill.name in enabled and skill.matches(path):
            return skill.text, skill.name, skill.skip_patterns
    return "", "", ()


def skill_template() -> str:
    """Return the bundled skill template text for users creating their own."""
    try:
        return (
            resources.files("tlumacz.skills")
            .joinpath(_SKILL_TEMPLATE_NAME)
            .read_text(encoding="utf-8")
        )
    except (ModuleNotFoundError, FileNotFoundError, TypeError, OSError):
        return _FALLBACK_TEMPLATE


def new_skill_file() -> Path:
    """Copy the template into the user skills directory as a new skill file.

    The name is unique (``moj-skilla.md``, then ``moj-skilla-2.md``, ...).
    Returns the created path.
    """
    target = user_skills_dir() / "moj-skilla.md"
    if target.exists():
        counter = 2
        while (user_skills_dir() / f"moj-skilla-{counter}.md").exists():
            counter += 1
        target = user_skills_dir() / f"moj-skilla-{counter}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(skill_template(), encoding="utf-8")
    return target


_FALLBACK_TEMPLATE = """---
name: Mój skilla
formats: md, markdown
skip_patterns:
---
<!--
Wymagane pola:
- name: nazwa skilla (unikalna, widoczna w GUI)
- formats: rozszerzenia plików oddzielone przecinkiem, np. md, markdown

Pole opcjonalne:
- skip_patterns: regexy (oddzielone przecinkiem) opisujące linie, których NIE
  wolno tłumaczyć dla tego formatu (np. metadane YAML, znaczniki stron).
  Puste = tylko uniwersalne bezpieczne wzorce.

Instrukcje poniżej są wstrzykiwane do promptu modelu dla pasujących plików.
-->
You are translating a document. Follow these rules:
- Preserve the exact structure: headings, lists, emphasis, links, tables.
- Do not translate code blocks, inline code, URLs or identifiers.
- Keep metadata lines unchanged.
- Translate only the prose content, faithfully and professionally.
"""


def _parse_skill(filename: str, text: str) -> Optional[Skill]:
    """Parse a skill file with optional ``---`` frontmatter."""
    meta: dict[str, str] = {}
    match = _FRONTMATTER_RE.match(text)
    if match:
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip().lower()] = value.strip()
        body = match.group(2)
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
    skip_patterns = tuple(
        pat.strip()
        for pat in meta.get("skip_patterns", "").split(",")
        if pat.strip()
    )
    return Skill(
        name=name,
        formats=formats,
        text=body.strip(),
        skip_patterns=skip_patterns,
    )