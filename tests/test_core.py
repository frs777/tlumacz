"""Tests for the core translation engine (Qt-free)."""

import os
import tempfile
import time

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
    assert _strip_eos_tokens("</html>\n<|im_start|>\n\n") == "</html>\n\n"
    assert _strip_eos_tokens("Treść.<|im_start|>reszta") == "Treść.reszta"


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


def _make_roundtrip_client():
    """Fake client that keeps ``⟦PROT_n⟧`` placeholders and translates the rest."""
    import re

    calls: list[dict] = []
    ph_re = re.compile(r"⟦PROT_\d+⟧")

    def create(**kwargs):
        calls.append(kwargs)
        content = kwargs["messages"][-1]["content"]
        parts = ph_re.split(content)
        phs = ph_re.findall(content)
        out = parts[0] if not parts[0].strip() else "PRZETŁUMACZONE"
        for ph, part in zip(phs, parts[1:]):
            out += ph + ("PRZETŁUMACZONE" if part.strip() else part)
        choice = type("C", (), {"message": type("M", (), {"content": out})()})()
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
    assert "Translate ALL passages that are not already in Polish" in prompt
    assert "must be translated" in prompt
    assert "preserving Markdown formatting" in prompt


def test_custom_prompt_replaces_default_but_glossary_appended(tmp_path):
    glossary = tmp_path / "g.csv"
    glossary.write_text("Hello,Witaj\n", encoding="utf-8")
    config = TranslatorConfig(system_prompt="Mój styl.", glossary_path=str(glossary))
    assert config.system_prompt.startswith("Mój styl.")
    assert "You are a professional" not in config.system_prompt
    assert config._glossary_prompt_for("no matching words here") == ""
    gloss = config._glossary_prompt_for("Hello there")
    assert "Hello => Witaj" in gloss
    assert "glossary list itself" in gloss


def test_translate_file_uses_skill_for_matching_format(tmp_path):
    client, _ = _make_fake_client()
    config = TranslatorConfig(enabled_skills=["Markdown"], chunk_size=200, cache_enabled=False)
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
    config = TranslatorConfig(enabled_skills=["Markdown"], chunk_size=200, cache_enabled=False)
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
    translator = Translator(TranslatorConfig(cache_enabled=False,chunk_size=10))
    translator.client = client
    source = tmp_path / "in.txt"
    source.write_text("a" * 100, encoding="utf-8")

    with pytest.raises(TranslationCancelledError):
        translator.translate_file(
            str(source),
            str(tmp_path / "out.txt"),
            is_cancelled=lambda: True,
        )


def test_cancel_interrupts_active_request(tmp_path):
    import threading

    class BlockingClient:
        def __init__(self):
            self.closed = threading.Event()
            self.started = threading.Event()

        class chat:
            pass

        def close(self):
            self.closed.set()

    client = BlockingClient()
    completions = type("Co", (), {})()

    def create(**kwargs):
        client.started.set()
        if not client.closed.wait(2):
            raise AssertionError("request was not interrupted")
        raise RuntimeError("request interrupted")

    completions.create = create
    client.chat = type("Ch", (), {"completions": completions})()

    translator = Translator(TranslatorConfig(cache_enabled=False))
    from unittest.mock import patch

    errors = []
    def run():
        try:
            translator._translate_chunk("tekst", "system prompt")
        except Exception as exc:  # cancellation is expected to interrupt the request
            errors.append(exc)

    thread = threading.Thread(target=run)
    with patch("tlumacz.core.openai.OpenAI", return_value=client):
        thread.start()
    assert client.started.wait(1)
    translator.cancel()
    thread.join(1)

    assert not thread.is_alive()
    assert client.closed.is_set()
    assert errors


def test_translate_file_missing_input(tmp_path):
    translator = Translator(TranslatorConfig(cache_enabled=False,))
    with pytest.raises(FileNotFoundError):
        translator.translate_file(
            str(tmp_path / "nope.txt"), str(tmp_path / "out.txt")
        )


def test_effective_skip_patterns_combines_skill_and_custom():
    translator = Translator(TranslatorConfig(cache_enabled=False,skip_line_patterns=[r"^CUSTOM$"]))
    assert translator._effective_skip_patterns((r"^SKILL$",)) == [
        r"^SKILL$",
        r"^CUSTOM$",
    ]


def test_effective_skip_patterns_defaults_when_skill_empty():
    translator = Translator(TranslatorConfig(cache_enabled=False,))
    assert translator._effective_skip_patterns(()) == list(DEFAULT_SKIP_PATTERNS)


def test_effective_skip_patterns_deduplicates():
    translator = Translator(TranslatorConfig(cache_enabled=False,))
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


def test_translate_file_parallel_preserves_order(tmp_path):
    import threading

    calls = []
    lock = threading.Lock()

    def create(**kwargs):
        content = kwargs["messages"][-1]["content"]
        with lock:
            calls.append(content)
        time.sleep(0.02 if "CHUNK 1" in content else 0.01)
        choice = type("C", (), {"message": type("M", (), {"content": content})()})()
        return type("R", (), {"choices": [choice]})()

    completions = type("Co", (), {"create": staticmethod(create)})()
    chat = type("Ch", (), {"completions": completions})()
    client = type("Cl", (), {"chat": chat, "calls": calls})()

    translator = Translator(TranslatorConfig(cache_enabled=False,chunk_size=20, parallel=3))
    translator.client = client
    source = tmp_path / "in.txt"
    source.write_text("CHUNK 1 123456789\nCHUNK 2 123456789\nCHUNK 3 123456789\n", encoding="utf-8")
    output = tmp_path / "out.txt"

    translator.translate_file(str(source), str(output))
    result = output.read_text(encoding="utf-8")
    assert result.index("CHUNK 1") < result.index("CHUNK 2") < result.index("CHUNK 3")
    assert len(calls) >= 2


def test_translate_file_parallel_disabled_matches_sequential(tmp_path):
    client, calls = _make_fake_client("OK")
    translator = Translator(TranslatorConfig(cache_enabled=False, chunk_size=10, parallel=1))
    translator.client = client
    source = tmp_path / "in.txt"
    source.write_text("abcdefghijabcdefghij", encoding="utf-8")
    output = tmp_path / "out.txt"

    translator.translate_file(str(source), str(output))
    assert output.read_text(encoding="utf-8").count("OK") == 2
    assert len(calls) == 2

def test_translate_file_binary_epub_roundtrip(tmp_path):
    import io
    import zipfile

    def _identity_create(**kwargs):
        calls.append(kwargs)
        content = kwargs["messages"][-1]["content"]
        choice = type("C", (), {"message": type("M", (), {"content": content})()})()
        return type("R", (), {"choices": [choice]})()

    calls: list[dict] = []
    completions = type("Co", (), {"create": staticmethod(_identity_create)})()
    chat = type("Ch", (), {"completions": completions})()
    client = type("Cl", (), {"chat": chat, "calls": calls})()

    html = (
        "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head><title>Rozdział</title></head>"
        "<body><h1>Rozdział 1</h1><p>To jest <b>tekst</b>.</p></body></html>"
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
        '<metadata><dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Book</dc:title></metadata>'
        '<manifest>'
        '<item id="nav" href="content.xhtml" media-type="application/xhtml+xml"/>'
        '<item id="img" href="cover.png" media-type="image/png"/>'
        '</manifest>'
        '<spine><itemref idref="nav"/></spine>'
        '</package>'
    )
    container = (
        '<?xml version="1.0"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/content.xhtml", html)
        z.writestr("OEBPS/cover.png", b"\x89PNG-binary-cover")
    source = tmp_path / "book.epub"
    source.write_bytes(buf.getvalue())
    output = tmp_path / "book_pl.epub"

    translator = Translator(TranslatorConfig(cache_enabled=False,enabled_skills=["HTML"]))
    translator.client = client
    translator.translate_file(str(source), str(output), log_callback=lambda _m: None)

    with zipfile.ZipFile(output) as z:
        names = z.namelist()
        assert names[0] == "mimetype"
        assert z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert z.read("OEBPS/cover.png") == b"\x89PNG-binary-cover"
        assert "OEBPS/content.opf" in names
        out_html = z.read("OEBPS/content.xhtml").decode("utf-8")

    assert "<h1>Rozdział 1</h1>" in out_html
    assert "To jest <b>tekst</b>." in out_html


def test_translate_file_binary_odt_input(tmp_path):
    import io
    import zipfile

    client, _ = _make_roundtrip_client()
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
    output = tmp_path / "out.odt"

    logs: list[str] = []
    translator.translate_file(str(source), str(output), log_callback=logs.append)

    assert any("odt" in line.lower() for line in logs)
    with zipfile.ZipFile(output, "r") as z:
        out_xml = z.read("content.xml").decode("utf-8")
    assert "<text:h>" in out_xml
    assert "<text:p>" in out_xml
    assert "PRZETŁUMACZONE" in out_xml


def test_translate_file_binary_docx_roundtrip(tmp_path):
    import io
    import zipfile

    client, _ = _make_roundtrip_client()
    config = TranslatorConfig(enabled_skills=["DOCX"], chunk_size=200)
    translator = Translator(config)
    translator.client = client

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body>'
        "<w:p><w:r><w:t>Treść do przetłumaczenia</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<?xml version=\"1.0\"?><Types/>")
        z.writestr("word/document.xml", doc_xml)
    source = tmp_path / "doc.docx"
    source.write_bytes(buf.getvalue())
    output = tmp_path / "out.docx"

    logs: list[str] = []
    translator.translate_file(str(source), str(output), log_callback=logs.append)

    assert any("docx" in line.lower() for line in logs)
    with zipfile.ZipFile(output, "r") as z:
        out_xml = z.read("word/document.xml").decode("utf-8")
        assert z.read("[Content_Types].xml").decode("utf-8") == '<?xml version="1.0"?><Types/>'
    assert "<w:t>PRZETŁUMACZONE</w:t>" in out_xml


def test_translate_text_empty_skip_patterns_translates_yaml(tmp_path):
    """EPUB must translate everything: no config/YAML skip patterns applied."""

    def _identity(**kwargs):
        calls.append(kwargs)
        content = kwargs["messages"][-1]["content"]
        choice = type("C", (), {"message": type("M", (), {"content": content})()})()
        return type("R", (), {"choices": [choice]})()

    calls: list[dict] = []
    completions = type("Co", (), {"create": staticmethod(_identity)})()
    chat = type("Ch", (), {"completions": completions})()
    translator = Translator(TranslatorConfig(cache_enabled=False,chunk_size=100))
    translator.client = type("Cl", (), {"chat": chat, "calls": calls})()

    text = "---\nname: foo\nlicense: MIT\n---\ntreść do przetłumaczenia"
    translator._translate_text(
        text, "", [],
        log=lambda _m: None,
    )

    sent = "\n".join(c["messages"][-1]["content"] for c in calls)
    assert "name: foo" in sent
    assert "license: MIT" in sent
    assert "---" in sent
    assert "treść do przetłumaczenia" in sent
