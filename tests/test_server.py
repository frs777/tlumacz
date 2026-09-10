"""Tests for the managed llama-server logic (Qt-free)."""

from tlumacz.server import LlamaServer, ServerConfig


def _server(chat_template: str = "") -> LlamaServer:
    return LlamaServer(
        ServerConfig(port=18080, gguf_path="/tmp/model.gguf", chat_template=chat_template)
    )


def test_template_attempts_default_jinja_then_chatml():
    assert _server()._template_attempts() == [None, "chatml"]


def test_template_attempts_config_chatml_first():
    assert _server("chatml")._template_attempts() == ["chatml", None]


def test_template_attempts_deduplicates():
    attempts = _server("chatml")._template_attempts()
    assert len(attempts) == len(set(attempts))
    assert None in attempts and "chatml" in attempts


def test_command_jinja_vs_chatml():
    jinja = _server()._command("llama-server", None)
    assert "--jinja" in jinja
    assert "--chat-template" not in jinja

    chatml = _server()._command("llama-server", "chatml")
    assert "--no-jinja" in chatml
    assert "--chat-template" in chatml
    assert chatml[chatml.index("--chat-template") + 1] == "chatml"


def test_command_includes_core_flags():
    cmd = _server()._command("llama-server", None)
    for flag in ("-m", "--alias", "--host", "--port", "--ctx-size", "--parallel"):
        assert flag in cmd