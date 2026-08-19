"""Tests for the core translation engine (Qt-free)."""

import os
import tempfile

import pytest

from tlumacz.core import (
    Translator,
    TranslatorConfig,
    TranslationCancelledError,
    _strip_eos_tokens,
)
from tlumacz.preprocess import DEFAULT_SKIP_PATTERNS
from tlumacz.skill import save_skill


def test_strip_eos_tokens():
    assert _strip_eos_tokens("Tekst.\n<|im_end|>") == "Tekst.\n"
    assert _strip_eos_tokens("Tekst.\n<|end_of_turn|>") == "Tekst.\n"
    assert _strip_eos_tokens("Tekst.</s>") == "Tekst."
    assert _strip_eos_tokens("Tekst.") == "Tekst."
    assert _strip_eos_tokens("<|im_end|>") == ""


class _FakeClient:
    def __init__(self, content: str = "PRZETŁUMACZONE"):
        self._content = content
        self.calls: list[list[dict]] = []

    class chat:
        pass

    def _completions(self, **kwargs):
        self.calls.append(kwargs)
        choice = type("C", (), {"message": type("M", (), {"content": self._content})()})()
        return type("R", (), {"choices": [choice]})()


def _make_fake_client(content: str = "PRZETŁUMACZONE"):
    outer = _FakeClient(content)
    calls: list[dict] = []

    def create(**kwargs):
        calls.append(kwargs)
        choice = type("C", (), {"message": type("M", (), {"content": content})()})()
        return type("R", (), {"choices": [choice]})()

    completions = type("Co", (), {"create": staticmethod(create)})()
    chat = type("Ch", (), {"completions": completions})()
    client = type("Cl", (), {"chat": chat, "calls": calls})()
    return client, calls


def test_split_into_chunks():
    config = TranslatorConfig(chunk_size=20)
    translator = Translator(config)
    text = "aaaa bbbb cccc dddd eeee\nffff gggg\n"
    chunks = translator._split_into_chunks(text)
    assert all(len(c) <= 20 or "\n" not in c for c in chunks)
    assert "".join(chunks) == text


def test_long_line_split_by_characters():
    config = TranslatorConfig(chunk_size=10)
    translator = Translator(config)
    text = "x" * 35
    chunks = translator._split_into_chunks(text)
    assert all(len(c) <= 10 for c in chunks)
    assert "".join(chunks) == text


def test_default_prompt_is_language_generic():
    config = TranslatorConfig(target_language="German")
    assert "German" in config.system_prompt
    assert "already in German" in config.system_prompt


def test_default_prompt_covers_multilingual_input():
    config = TranslatorConfig(target_language="Polish")
    prompt = config.system_prompt
    assert "more than one language" in prompt
    assert "Every sentence in another" in prompt
    assert "must be translated" in prompt


def test_custom_prompt_replaces_default_but_glossary_appended(tmp_path):
    glossary = tmp_path / "g.csv"
    glossary.write_text("Hello,Witaj\n", encoding="utf-8")
    config = TranslatorConfig(system_prompt="Mój styl.", glossary_path=str(glossary))
    assert config.system_prompt.startswith("Mój styl.")
    assert "Hello => Witaj" in config.system_prompt
    assert "You are a professional" not in config.system_prompt


def test_translate_file_uses_skill_for_matching_format(tmp_path):
    client, _ = _make_fake_client()
    config = TranslatorConfig(enabled_skills=["Markdown"], chunk_size=200)
    translator = Translator(config)
    translator.client = client

    source = tmp_path / "doc.md"
    source.write_text("# Nagłówek\n\nTekst.\n", encoding="utf-8")
    output = tmp_path / "out.md"

    logs: list[str] = []
    translator.translate_file(str(source), str(output), log_callback=logs.append)
    assert any("skill: Markdown" in line for line in logs)
    system = client.calls[0]["messages"][0]["content"]
    assert "fenced code blocks" in system


def test_translate_file_skips_skill_for_other_format(tmp_path):
    client, _ = _make_fake_client()
    config = TranslatorConfig(enabled_skills=["Markdown"], chunk_size=200)
    translator = Translator(config)
    translator.client = client

    source = tmp_path / "doc.txt"
    source.write_text("Tekst.\n", encoding="utf-8")
    output = tmp_path / "out.txt"

    logs: list[str] = []
    translator.translate_file(str(source), str(output), log_callback=logs.append)
    assert not any("skill:" in line for line in logs)
    system = client.calls[0]["messages"][0]["content"]
    assert "fenced code blocks" not in system


def test_translate_file_cancellation(tmp_path):
    client, _ = _make_fake_client()
    translator = Translator(TranslatorConfig(chunk_size=10))
    translator.client = client
    source = tmp_path / "in.txt"
    source.write_text("a" * 100, encoding="utf-8")

    with pytest.raises(TranslationCancelledError):
        translator.translate_file(
            str(source),
            str(tmp_path / "out.txt"),
            is_cancelled=lambda: True,
        )


def test_translate_file_missing_input(tmp_path):
    translator = Translator(TranslatorConfig())
    with pytest.raises(FileNotFoundError):
        translator.translate_file(
            str(tmp_path / "nope.txt"), str(tmp_path / "out.txt")
        )


def test_effective_skip_patterns_combines_skill_and_custom():
    translator = Translator(TranslatorConfig(skip_line_patterns=[r"^CUSTOM$"]))
    assert translator._effective_skip_patterns((r"^SKILL$",)) == [
        r"^SKILL$",
        r"^CUSTOM$",
    ]


def test_effective_skip_patterns_defaults_when_skill_empty():
    translator = Translator(TranslatorConfig())
    assert translator._effective_skip_patterns(()) == list(DEFAULT_SKIP_PATTERNS)


def test_effective_skip_patterns_deduplicates():
    translator = Translator(TranslatorConfig())
    eff = translator._effective_skip_patterns(tuple(DEFAULT_SKIP_PATTERNS))
    assert eff == list(DEFAULT_SKIP_PATTERNS)


def test_translate_file_uses_skill_skip_patterns(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    save_skill("", "TestSkip", "md, markdown", "Instrukcje.", "^KEEP_ME$")
    client, _ = _make_fake_client("PRZETŁUMACZONE")
    config = TranslatorConfig(enabled_skills=["TestSkip"], chunk_size=200)
    translator = Translator(config)
    translator.client = client

    source = tmp_path / "doc.md"
    source.write_text("KEEP_ME\nNormalna linia.\n", encoding="utf-8")
    output = tmp_path / "out.md"

    logs: list[str] = []
    translator.translate_file(str(source), str(output), log_callback=logs.append)

    result = output.read_text(encoding="utf-8")
    assert "KEEP_ME" in result
    assert "PRZETŁUMACZONE" in result
    assert any("skill: TestSkip" in line for line in logs)


def test_translate_file_binary_odt_input(tmp_path):
    import io
    import zipfile

    client, _ = _make_fake_client("PRZETŁUMACZONE")
    config = TranslatorConfig(enabled_skills=["ODT"], chunk_size=200)
    translator = Translator(config)
    translator.client = client

    xml = (
        '<office:document-content xmlns:office='
        '"urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text='
        '"urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        "<office:body><office:text>"
        "<text:h>Nagłówek</text:h><text:p>Akapit.</text:p>"
        "</office:text></office:body></office:document-content>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("content.xml", xml)
    source = tmp_path / "doc.odt"
    source.write_bytes(buf.getvalue())
    output = tmp_path / "out.md"

    logs: list[str] = []
    translator.translate_file(str(source), str(output), log_callback=logs.append)

    assert any("odt" in line.lower() for line in logs)
    assert output.read_text(encoding="utf-8") == "PRZETŁUMACZONE\n\n"
