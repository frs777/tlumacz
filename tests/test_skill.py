"""Tests for bundled translation skill discovery and matching."""

from tlumacz.skill import Skill, discover_skills, save_skill, text_for_file


def test_discover_finds_bundled_skills():
    names = {s.name for s in discover_skills()}
    assert {"Markdown", "Tekst zwykły", "HTML"} <= names


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
    text, name = text_for_file("notes.txt", enabled=["Tekst zwykły"])
    assert name == "Tekst zwykły"
    assert "plain text" in text.lower()


def test_text_for_file_disabled_or_nonmatching():
    assert text_for_file("x.md", enabled=[]) == ("", "")
    assert text_for_file("x.unknown", enabled=["Markdown"]) == ("", "")


def test_parse_missing_frontmatter_fields():
    from tlumacz.skill import _parse_skill

    assert _parse_skill("bad.md", "no frontmatter here") is None
    assert _parse_skill("bad.md", "---\nname: X\n---\nbody") is None
    assert _parse_skill("bad.md", "---\nformats: md\n---\nbody") is None
    good = _parse_skill("ok.md", "---\nname: X\nformats: md, txt\n---\nbody text")
    assert good == Skill(name="X", formats=("md", "txt"), text="body text")


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
    text, name = text_for_file("x.md", ["Markdown"])
    assert name == "Markdown"
    assert text.startswith("USER OVERRIDE")


def test_user_skill_ignored_without_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from tlumacz.skill import user_skills_dir

    d = user_skills_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "no-formats.md").write_text(
        "---\ndescription: bez formats\n---\nbody", encoding="utf-8"
    )
    names = {s.name for s in discover_skills()}
    assert "no-formats" not in names
