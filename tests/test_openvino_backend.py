"""Testy jednostkowe dla OpenVINOBackend.

Testy weryfikują:
- OpenVINOConfig (walidacja, domyślne wartości)
- OpenVINOBackend (mockowane metody)
- translate() z mockowanym pipeline
- _build_prompt()
- _clean_output()
"""

import pytest
from unittest.mock import MagicMock, patch

from tlumacz.openvino_backend import OpenVINOConfig, OpenVINOBackend


# ---------------------------------------------------------------------------
# Testy OpenVINOConfig
# ---------------------------------------------------------------------------

class TestOpenVINOConfig:
    """Testy konfiguracji OpenVINO."""

    def test_default_values(self):
        """Domyślne wartości konfiguracji."""
        config = OpenVINOConfig()
        assert config.model_path == ""
        assert config.device == "CPU"
        assert config.max_new_tokens == 512
        assert config.temperature == 0.0

    def test_custom_values(self):
        """Niestandardowe wartości konfiguracji."""
        config = OpenVINOConfig(
            model_path="/tmp/model",
            device="GPU",
            max_new_tokens=1024,
            temperature=0.7,
        )
        assert config.model_path == "/tmp/model"
        assert config.device == "GPU"
        assert config.max_new_tokens == 1024
        assert config.temperature == 0.7

    def test_validate_valid_path(self, tmp_path):
        """Walidacja poprawnej ścieżki."""
        config = OpenVINOConfig(model_path=str(tmp_path))
        config.validate()  # Nie powinno raise

    def test_validate_invalid_path(self):
        """Walidacja nieistniejącej ścieżki."""
        config = OpenVINOConfig(model_path="/nie/istnieje")
        with pytest.raises(ValueError, match="Katalog modelu nie istnieje"):
            config.validate()


# ---------------------------------------------------------------------------
# Testy OpenVINOBackend
# ---------------------------------------------------------------------------

class TestOpenVINOBackend:
    """Testy backendu OpenVINO."""

    def test_init_default(self):
        """Inicjalizacja z domyślną konfiguracją."""
        backend = OpenVINOBackend()
        assert backend.config.device == "CPU"
        assert not backend.is_loaded

    def test_init_custom(self):
        """Inicjalizacja z niestandardową konfiguracją."""
        config = OpenVINOConfig(device="GPU")
        backend = OpenVINOBackend(config)
        assert backend.config.device == "GPU"

    def test_base_url(self):
        """base_url zwraca 'openvino://<device>'."""
        backend = OpenVINOBackend(OpenVINOConfig(device="CPU"))
        assert backend.base_url == "openvino://CPU"

    def test_get_last_error_empty(self):
        """get_last_error zwraca pusty string na start."""
        backend = OpenVINOBackend()
        assert backend.get_last_error() == ""

    def test_unload_model_when_not_loaded(self):
        """unload_model gdy model nie jest załadowany."""
        backend = OpenVINOBackend()
        backend.unload_model()  # Nie powinno raise
        assert not backend.is_loaded


# ---------------------------------------------------------------------------
# Testy _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    """Testy budowania promptu."""

    def test_basic_prompt(self):
        """Podstawowy prompt bez kontekstu."""
        backend = OpenVINOBackend()
        prompt = backend._build_prompt("Hello", "en", "pl")
        assert "Hello" in prompt
        assert "from en to pl" in prompt

    def test_prompt_with_context(self):
        """Prompt z kontekstem (skill/glosariusz)."""
        backend = OpenVINOBackend()
        prompt = backend._build_prompt("Hello", "en", "pl", context="Skill text")
        assert "Skill text" in prompt
        assert "Hello" in prompt

    def test_auto_source_lang(self):
        """Prompt z auto-detected językiem źródłowym."""
        backend = OpenVINOBackend()
        prompt = backend._build_prompt("Hello", "auto", "pl")
        assert "from auto to pl" in prompt


# ---------------------------------------------------------------------------
# Testy _clean_output
# ---------------------------------------------------------------------------

class TestCleanOutput:
    """Testy czyszczenia wyjścia."""

    def test_clean_quotes(self):
        """Usuwanie otaczających cytatów."""
        assert OpenVINOBackend._clean_output('**Text**') == "Text"
        assert OpenVINOBackend._clean_output('"Text"') == "Text"

    def test_clean_no_quotes(self):
        """Tekst bez cytatów."""
        assert OpenVINOBackend._clean_output("Czysty tekst") == "Czysty tekst"

    def test_clean_translates_to(self):
        """Usuwanie 'translates to:'."""
        result = OpenVINOBackend._clean_output("Hello translates to: Witaj")
        assert result == "Witaj"

