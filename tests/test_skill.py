"""Tests for bundled translation skill discovery and matching."""

import pytest

from tlumacz.skill import (
    Skill,
    discover_skills,
    new_skill_file,
    save_skill,
    skill_template,
    text_for_file,
    user_skills_dir,
)


def test_discover_finds_bundled_skills():
    names = {s.name for s in discover_skills()}
    assert {"Markdown", "Tekst zwykły", "HTML"} <= names


def test_template_not_discovered_as_skill():
    names = {s.name for s in discover_skills()}
    assert "SKILL_TEMPLATE" not in names


def test_skills_sorted_and_parseable():
    skills = discover_skills()
    assert skills == sorted(skills, key=lambda s: s.name.casefold())
    for skill in skills:
        assert skill.name
        assert skill.formats
        assert skill.text


def test_matching_by_extension():
    markdown = next(s for s in discover_skills() if s.name == "Markdown")
    assert markdown.matches("readme.md")
    assert markdown.matches("/x/y/READ.ME.MD")
    assert not markdown.matches("readme.txt")


def test_text_for_file_enabled_and_matching():
    text, name, patterns = text_for_file("notes.txt", enabled=["Tekst zwykły"])
    assert name == "Tekst zwykły"
    assert "plain text" in text.lower()
    assert patterns == ()


def test_text_for_file_disabled_or_nonmatching():
    assert text_for_file("x.md", enabled=[]) == ("", "", ())
    assert text_for_file("x.unknown", enabled=["Markdown"]) == ("", "", ())


def test_markdown_skill_has_skip_patterns():
    markdown = next(s for s in discover_skills() if s.name == "Markdown")
    assert markdown.skip_patterns
    text, name, patterns = text_for_file("x.md", enabled=["Markdown"])
    assert name == "Markdown"
    assert patterns == markdown.skip_patterns


def test_parse_missing_frontmatter_fields():
    from tlumacz.skill import _parse_skill

    assert _parse_skill("bad.md", "no frontmatter here") is None
    assert _parse_skill("bad.md", "---\nname: X\n---\nbody") is None
    assert _parse_skill("bad.md", "---\nformats: md\n---\nbody") is None
    good = _parse_skill("ok.md", "---\nname: X\nformats: md, txt\n---\nbody text")
    assert good == Skill(name="X", formats=("md", "txt"), text="body text")


def test_parse_skip_patterns():
    from tlumacz.skill import _parse_skill

    good = _parse_skill(
        "ok.md",
        "---\nname: X\nformats: md\n"
        "skip_patterns: ^foo, bar$, ^\\s*---\\s*$\n---\nbody",
    )
    assert good is not None
    assert good.skip_patterns == ("^foo", "bar$", "^\\s*---\\s*$")


def test_user_skill_loaded_from_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_skill("", "Mój skilla", "md, markdown", "Instrukcje.")
    names = {s.name for s in discover_skills()}
    assert "Mój skilla" in names


def test_user_skill_overrides_bundled(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_skill("", "Markdown", "md, markdown", "USER OVERRIDE")
    markdown = next(s for s in discover_skills() if s.name == "Markdown")
    assert markdown.text.startswith("USER OVERRIDE")
    text, name, _ = text_for_file("x.md", ["Markdown"])
    assert name == "Markdown"
    assert text.startswith("USER OVERRIDE")


def test_user_skill_ignored_without_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    d = user_skills_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "no-formats.md").write_text(
        "---\ndescription: bez formats\n---\nbody", encoding="utf-8"
    )
    names = {s.name for s in discover_skills()}
    assert "no-formats" not in names


def test_save_skill_writes_skip_patterns(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_skill("", "PDF", "pdf", "Instrukcje.", "^Strona \\d+$")
    skill = next(s for s in discover_skills() if s.name == "PDF")
    assert skill.skip_patterns == ("^Strona \\d+$",)


def test_skill_template_is_valid_skill(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    text = skill_template()
    assert "name:" in text and "formats:" in text
    target = new_skill_file()
    assert target.exists()
    skill = next(s for s in discover_skills() if s.name == "Mój skilla")
    assert skill.text  # template body parses as a valid skill


def test_new_skill_file_unique_name(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    first = new_skill_file()
    second = new_skill_file()
    assert first != second
    assert first.exists() and second.exists()
    assert (user_skills_dir() / "moj-skilla.md") == first
    assert (user_skills_dir() / "moj-skilla-2.md") == second
