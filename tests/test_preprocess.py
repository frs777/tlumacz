"""Tests for preprocessing: protection, line filtering, section chunking."""

import pytest

from tlumacz.core import Translator, TranslatorConfig
from tlumacz.preprocess import (
    DEFAULT_SKIP_PATTERNS,
    is_skipped,
    protect,
    restore,
    split_segments,
)


def test_protect_fenced_code_roundtrip():
    src = 'Text before.\n```python\nprint("hi")\n```\nText after.'
    masked, originals = protect(src)
    assert "print(" not in masked
    assert "```" not in masked
    assert restore(masked, originals) == src


def test_protect_inline_code_and_urls():
    src = "Użyj `pip install foo` i zobacz https://example.com/x."
    masked, originals = protect(src)
    assert "pip install" not in masked
    assert "example.com" not in masked
    assert restore(masked, originals) == src


def test_restore_leaves_unknown_placeholders():
    assert restore("x ⟦PROT_99⟧ y", ["a"]) == "x ⟦PROT_99⟧ y"


def test_default_skip_patterns_match_yaml_metadata():
    compiled = [__import__("re").compile(p) for p in DEFAULT_SKIP_PATTERNS]
    assert is_skipped("license: MIT", compiled)
    assert is_skipped("  version: \"1.2.2\"", compiled)
    assert is_skipped("---", compiled)
    assert not is_skipped('description: "Długi opis"', compiled)
    assert not is_skipped("Jakiś zwykły tekst.", compiled)


def test_split_segments_keep_metadata_lines():
    text = (
        "---\n"
        "name: demo\n"
        'description: "Opis do tłumaczenia"\n'
        "license: MIT\n"
        "---\n"
        "# Tytuł\n"
        "Treść akapitu.\n"
    )
    segments = split_segments(text, chunk_size=100, skip_patterns=DEFAULT_SKIP_PATTERNS)
    kinds = [k for k, _ in segments]
    assert "keep" in kinds
    kept = [c for k, c in segments if k == "keep"]
    assert "---" in kept
    assert "license: MIT" in kept
    translated = [c for k, c in segments if k == "translate"]
    assert any("description" in c for c in translated)
    assert any("Tytuł" in c for c in translated)


def test_split_segments_heading_starts_new_chunk():
    long_para = "słowo " * 40  # 240 chars -> fills > 60% of a 300-char chunk
    text = f"{long_para}\n\n# Nagłówek\n\ndrugi akapit\n"
    segments = split_segments(text, chunk_size=300, skip_patterns=())
    translated = [c for k, c in segments if k == "translate"]
    assert any(c.startswith("# Nagłówek") for c in translated)
    for c in translated:
        if c.startswith("# Nagłówek"):
            assert not c.startswith("słowo")
    joined = "".join(c + "\n" for _, c in segments)
    assert "# Nagłówek" in joined
    assert joined.index("# Nagłówek") < joined.index("drugi akapit")


def test_split_segments_groups_small_headings_into_one_chunk():
    text = "# A\n\nkrotki akapit.\n\n## B\n\nkrotki akapit.\n\n### C\n\nkrotki akapit.\n"
    segments = split_segments(text, chunk_size=2000, skip_patterns=())
    translated = [c for k, c in segments if k == "translate"]
    assert len(translated) == 1
    assert "# A" in translated[0]
    assert "## B" in translated[0]
    assert "### C" in translated[0]


def test_split_segments_keeps_section_together_on_overflow():
    long_para = "word " * 40
    text = f"# Tytul\n\n{long_para}\n\n## Nastepna\n\nmore text here.\n"
    segments = split_segments(text, chunk_size=200, skip_patterns=())
    translated = [c for k, c in segments if k == "translate"]
    assert any("# Tytul" in c for c in translated)
    # the section with the long paragraph stays in one translate segment
    assert any(long_para.strip() in c for c in translated)


def test_split_segments_respects_chunk_size():
    lines = [f"linia {i} " + "x" * 20 for i in range(30)]
    text = "\n".join(lines)
    segments = split_segments(text, chunk_size=120, skip_patterns=())
    for kind, content in segments:
        if kind == "translate":
            assert len(content) <= 120 or "\n" not in content
    joined = "\n".join(c for _, c in segments)
    pos = -1
    for line in lines:
        found = joined.find(line, pos + 1)
        assert found > pos
        pos = found


def test_translate_file_protects_and_restores_code(tmp_path):
    client = _make_client_with_echo()
    translator = Translator(TranslatorConfig(chunk_size=200))
    translator.client = client
    src = tmp_path / "doc.md"
    src.write_text(
        "# Tytuł\n\n```python\nkeep = 'me'\n```\n\nDalszy tekst.\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.md"
    translator.translate_file(str(src), str(out))
    result = out.read_text(encoding="utf-8")
    assert "keep = 'me'" in result
    assert "```python" in result


def _make_client_with_echo():
    calls: list[dict] = []

    def create(**kwargs):
        calls.append(kwargs)
        # Echo the user content back so placeholders/skips survive.
        user = kwargs["messages"][-1]["content"]
        body = user.split("\n\n", 1)[1] if "\n\n" in user else user
        choice = type("C", (), {"message": type("M", (), {"content": body})()})()
        return type("R", (), {"choices": [choice]})()

    completions = type("Co", (), {"create": staticmethod(create)})()
    chat = type("Ch", (), {"completions": completions})()
    return type("Cl", (), {"chat": chat, "calls": calls})()