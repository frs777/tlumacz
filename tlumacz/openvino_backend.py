"""Backend OpenVINO dla TranslateGemma.

Implementuje backend tłumaczenia używający OpenVINO Runtime z modelem
TranslateGemma 4B INT8 zoptymalizowanym dla CPU AMD.

Moduł jest opcjonalny — import nie powiedzie się jeśli openvino-genai
nie jest zainstalowane. BackendManager obsługuje ten przypadek gracefulnie.

Wymaga:
    pip install openvino openvino-genai
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OpenVINOConfig:
    """Konfiguracja backendu OpenVINO.

    Atrybuty:
        model_path: Ścieżka do katalogu z modelem OpenVINO IR.
        device: Urządzenie wykonawcze — "CPU", "GPU", "AUTO".
        max_new_tokens: Maksymalna liczba tokenów do wygenerowania.
        temperature: Temperatura generowania (0 = greedy).
    """

    model_path: str = ""
    device: str = "CPU"
    max_new_tokens: int = 512
    temperature: float = 0.0

    def validate(self) -> None:
        """Sprawdź poprawność konfiguracji.

        Raises:
            ValueError: Jeśli ścieżka do modelu nie istnieje.
        """
        if not Path(self.model_path).is_dir():
            raise ValueError(
                f"Katalog modelu nie istnieje: {self.model_path}. "
                "Pobierz model: hf download light434/translategemma-4b-it-int8-ov "
                "--local-dir ~/Modele/openvino/translategemma-4b-it-int8-ov"
            )


# Mapowanie kodów ISO 639-1 na pełne nazwy języków (dla promptu)
_LANG_NAMES = {
    "pl": "Polish", "en": "English", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian",
    "ru": "Russian", "uk": "Ukrainian", "cs": "Czech",
    "sk": "Slovak", "pt": "Portuguese", "nl": "Dutch",
    "sv": "Swedish", "da": "Danish", "fi": "Finnish",
    "no": "Norwegian", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese", "ar": "Arabic", "tr": "Turkish",
    "auto": "auto-detected",
}


class OpenVINOBackend:
    """Backend tłumaczenia używający OpenVINO Runtime.

    Obsługuje model TranslateGemma 4B INT8 zoptymalizowany dla OpenVINO.
    Wspiera urządzenia: CPU (AMD Ryzen), GPU (Intel iGPU), AUTO.

    Example:
        >>> config = OpenVINOConfig(device="CPU")
        >>> backend = OpenVINOBackend(config)
        >>> backend.load_model()
        True
        >>> backend.translate("Hello world", "en", "pl")
        'Witaj świecie'
    """

    def __init__(self, config: Optional[OpenVINOConfig] = None) -> None:
        self._config = config or OpenVINOConfig()
        self._pipe = None
        self._is_loaded = False
        self._load_time = 0.0
        self._last_error = ""

    @property
    def config(self) -> OpenVINOConfig:
        """Konfiguracja backendu."""
        return self._config

    @property
    def is_loaded(self) -> bool:
        """Czy model jest załadowany."""
        return self._is_loaded

    @property
    def device(self) -> str:
        """Aktywne urządzenie wykonawcze."""
        return self._config.device

    @property
    def base_url(self) -> str:
        """Pseudo-URL dla kompatybilności z BackendManager."""
        return f"openvino://{self._config.device}"

    def load_model(self) -> bool:
        """Załaduj model OpenVINO.

        Returns:
            True jeśli model załadowany pomyślnie.

        Raises:
            RuntimeError: Jeśli model nie może być załadowany.
        """
        if self._is_loaded:
            logger.info("Model OpenVINO już załadowany")
            return True

        try:
            import openvino_genai as ov_genai

            logger.info("Ładowanie modelu OpenVINO z %s na %s", self._config.model_path, self._config.device)
            start = time.time()

            try:
                self._pipe = ov_genai.VLMPipeline(
                    self._config.model_path,
                    self._config.device,
                )
            except Exception as device_exc:
                # Fallback: jeśli GPU failuje (np. AMD iGPU nie wspierane), spróbuj CPU
                if self._config.device in ("GPU", "AUTO", "MULTI:CPU,GPU"):
                    logger.warning(
                        "Urządzenie %s nie dostępne (%s), fallback na CPU",
                        self._config.device, device_exc,
                    )
                    self._config.device = "CPU"
                    self._pipe = ov_genai.VLMPipeline(
                        self._config.model_path,
                        "CPU",
                    )
                else:
                    raise

            # Chat template: passthrough — prompt budujemy ręcznie
            self._pipe.set_chat_template("{{ bos_token }}{{ messages[-1]['content'] }}")

            self._load_time = time.time() - start
            self._is_loaded = True

            logger.info(
                "Model OpenVINO załadowany w %.1fs na %s",
                self._load_time, self._config.device,
            )
            return True

        except ImportError as exc:
            self._last_error = f"Brak openvino-genai: {exc}"
            logger.error(self._last_error)
            raise RuntimeError(
                "OpenVINO nie jest zainstalowane. "
                "Zainstaluj: pip install openvino openvino-genai"
            ) from exc
        except Exception as exc:
            self._last_error = f"Błąd ładowania modelu: {exc}"
            logger.error(self._last_error)
            raise RuntimeError(
                f"Nie można załadować modelu OpenVINO: {exc}"
            ) from exc

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "pl",
        max_new_tokens: Optional[int] = None,
        context: str = "",
    ) -> str:
        """Przetłumacz tekst.

        Args:
            text: Tekst do tłumaczenia.
            source_lang: Kod języka źródłowego (ISO 639-1) lub "auto".
            target_lang: Kod języka docelowego (ISO 639-1).
            max_new_tokens: Maksymalna liczba tokenów (override config).
            context: Dodatkowy kontekst (glosariusz, skill, system prompt).

        Returns:
            Przetłumaczony tekst.

        Raises:
            RuntimeError: Jeśli model nie jest załadowany.
        """
        if not self._is_loaded or self._pipe is None:
            raise RuntimeError(
                "Model nie jest załadowany. Wywołaj load_model() najpierw."
            )

        try:
            prompt = self._build_prompt(text, source_lang, target_lang, context)

            cfg = self._pipe.get_generation_config()
            cfg.max_new_tokens = max_new_tokens or self._config.max_new_tokens
            cfg.max_length = 4096 + cfg.max_new_tokens
            cfg.do_sample = self._config.temperature > 0
            if cfg.do_sample:
                cfg.temperature = self._config.temperature
            cfg.apply_chat_template = False
            cfg.stop_token_ids = {1, 106}  # <eos>, <end_of_turn>

            # Rozpocznij sesję czatu — wymagane dla VLMPipeline
            self._pipe.start_chat()

            try:
                start = time.time()
                result = self._pipe.generate(prompt, generation_config=cfg)
                elapsed = time.time() - start
            finally:
                # Zakończ sesję czatu — zwolnij infer request
                self._pipe.finish_chat()

            # VLMDecodedResults — wyciągnij tekst z listy
            if hasattr(result, "texts") and result.texts:
                translation = result.texts[0]
            else:
                translation = str(result)

            # Wyczyść odpowiedź z ewentualnych nadmiarowych sformatowań
            translation = self._clean_output(translation)

            logger.debug(
                "Tłumaczenie OpenVINO: %.1fs (%d → %d znaków)",
                elapsed, len(text), len(translation),
            )
            return translation

        except Exception as exc:
            self._last_error = f"Błąd tłumaczenia: {exc}"
            logger.error(self._last_error)
            # Cleanup po błędzie — upewnij się że sesja jest zakończona
            try:
                if self._pipe is not None:
                    self._pipe.finish_chat()
            except Exception:
                pass  # Ignoruj błędy cleanup
            raise RuntimeError(f"Tłumaczenie nie powiodło się: {exc}") from exc

    def _build_prompt(self, text: str, source_lang: str, target_lang: str, context: str = "") -> str:
        """Zbuduj prompt w formacie TranslateGemma.

        Prompt używa kodów języków ISO 639-1 (en, pl) zamiast pełnych nazw
        — TranslateGemma lepiej rozumie kody językowe.
        """
        # Użyj kodów języków zamiast pełnych nazw (lepsza jakość)
        source_code = source_lang if source_lang else "auto"
        target_code = target_lang if target_lang else "pl"

        # Wstaw kontekst jeśli podany
        context_block = ""
        if context and context.strip():
            context_block = f"\n\nAdditional instructions:\n{context.strip()}\n"

        return (
            "<start_of_turn>user\n"
            f"You are a professional translator. "
            f"Translate ALL text from {source_code} to {target_code}. "
            "Translate EVERY SINGLE WORD and sentence. "
            "Do NOT skip any content. "
            "Never leave text in the source language. "
            "Complete the entire translation — do not stop early. "
            "Preserve document structure, formatting, headers, and sections. "
            "Produce ONLY the translation, without explanations or commentary."
            f"{context_block}\n\n"
            f"{text}"
            "<end_of_turn>\n"
            "<start_of_turn>model\n"
        )

    @staticmethod
    def _clean_output(text: str) -> str:
        """Wyczyść odpowiedź modelu z nadmiarowych sformatowań.

        Model może dodać markdown, cytaty, lub objaśnienia mimo instrukcji.
        Ta metoda próbuje wyciągnąć czyste tłumaczenie.
        """
        result = text.strip()

        # Usuń otaczające cytaty (**text** lub "text")
        if result.startswith("**") and result.endswith("**") and result.count("**") == 2:
            result = result[2:-2].strip()
        if result.startswith('"') and result.endswith('"') and result.count('"') == 2:
            result = result[1:-1].strip()

        # Jeśli odpowiedź zawiera "translates to:" — weź tylko po tej frazie
        for marker in ("translates to:", "translation:", "Translation:"):
            if marker in result:
                idx = result.index(marker) + len(marker)
                result = result[idx:].strip()
                # Ponownie usuń cytaty
                if result.startswith("**") and result.endswith("**") and result.count("**") == 2:
                    result = result[2:-2].strip()
                break

        return result.strip()

    def unload_model(self) -> None:
        """Zwolnij model z pamięci."""
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
        self._is_loaded = False
        logger.info("Model OpenVINO zwolniony z pamięci")

    def get_last_error(self) -> str:
        """Zwraca ostatni błąd."""
        return self._last_error

    def get_ram_usage_mb(self) -> int:
        """Zwraca zużycie RAM w MB (proces)."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss // 1024 // 1024
        except ImportError:
            return 0
