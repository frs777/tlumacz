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

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Optional

from .qt_gui.config import config_dir


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
    """Return the bundled and user skills, sorted by name for a stable order.

    User skills from ``<config_dir>/skills/`` win over bundled ones with the
    same name.
    """
    by_name: dict[str, Skill] = {}

    def collect(entries: Iterable[Path]) -> None:
        for entry in entries:
            if entry.name.lower().endswith(".md"):
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


def save_skill(path: str | Path, name: str, formats: str, text: str) -> Path:
    """Write a user skill file into the user skills directory.

    The filename is derived from the skill name (lowercased, non-alphanumeric
    characters replaced with ``-``). Returns the created path.
    """
    target = user_skills_dir() / _slugify(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"---\nname: {name}\nformats: {formats}\n---\n\n{text.strip()}\n",
        encoding="utf-8",
    )
    return target


def _slugify(name: str) -> str:
    safe = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return (safe or "skill") + ".md"


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