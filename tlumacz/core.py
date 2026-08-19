"""Core translation logic for Tłumacz.

This module is intentionally free of Qt/CLI dependencies so it can be reused
by the GUI, future CLI versions, and installed globally as a Python package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

import openai

from .glossary import Glossary, MAX_PROMPT_ENTRIES
from .skill import text_for_file


@dataclass
class TranslatorConfig:
    """Configuration for the OpenAI-compatible translation backend."""

    base_url: str = "http://127.0.0.1:8080/v1"
    api_key: str = "ollama"
    model: str = "qwen2.5-coder-7b-instruct-q5_k_m"
    chunk_size: int = 4000
    temperature: float = 0.1
    target_language: str = "Polish"
    system_prompt: Optional[str] = None
    glossary_path: Optional[str] = None
    enabled_skills: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        base = self.system_prompt
        if base is None:
            base = (
                "You are a professional technical translator. "
                f"Translate the provided text into {self.target_language} "
                "while preserving Markdown formatting. "
                f"If the text is already in {self.target_language}, return it "
                "unchanged without translating it again."
            )
        glossary_text = self._load_glossary_text()
        if glossary_text:
            base = base.rstrip() + "\n\n" + glossary_text
        self.system_prompt = base

    def _load_glossary_text(self) -> str:
        """Return the glossary prompt fragment, or ``""`` when not usable."""
        if not self.glossary_path:
            return ""
        try:
            glossary = Glossary.from_csv(
                self.glossary_path, max_entries=MAX_PROMPT_ENTRIES
            )
            return glossary.to_prompt()
        except OSError:
            return ""


class TranslationCancelledError(Exception):
    """Raised when the user cancels a running translation."""


class Translator:
    """Translate files using an OpenAI-compatible chat completions API."""

    def __init__(self, config: TranslatorConfig) -> None:
        self.config = config
        self.client = openai.OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks without breaking lines when possible.

        If a single line exceeds ``chunk_size`` it is split by characters.
        """
        lines = text.splitlines(keepends=True)
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for line in lines:
            line_len = len(line)
            if line_len > self.config.chunk_size:
                if current:
                    chunks.append("".join(current))
                    current = []
                    current_len = 0
                for i in range(0, line_len, self.config.chunk_size):
                    chunks.append(line[i : i + self.config.chunk_size])
                continue

            if current_len + line_len > self.config.chunk_size:
                chunks.append("".join(current))
                current = [line]
                current_len = line_len
            else:
                current.append(line)
                current_len += line_len

        if current:
            chunks.append("".join(current))

        return chunks

    def _translate_chunk(self, chunk: str, skill_text: str = "") -> str:
        """Translate a single chunk via the configured API."""
        system = self.config.system_prompt
        if skill_text:
            system = system.rstrip() + "\n\n" + skill_text
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        f"Translate the following text into {self.config.target_language}, "
                        "preserving Markdown formatting:\n\n"
                        f"{chunk}"
                    ),
                },
            ],
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content or ""

    def translate_file(
        self,
        input_path: str,
        output_path: str,
        *,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> None:
        """Translate ``input_path`` and write the result to ``output_path``.

        Args:
            input_path: Path to the file to translate.
            output_path: Path where the translated file will be written.
            progress_callback: Called as ``progress_callback(current, total)``
                after each chunk finishes.
            log_callback: Called with human-readable status messages.
            is_cancelled: Callable that returns ``True`` when the operation
                should be aborted. Checked before each chunk.

        Raises:
            FileNotFoundError: If the input file does not exist.
            TranslationCancelledError: If ``is_cancelled`` returns ``True``.
            openai.OpenAIError: If an API call fails and is not recoverable.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = self._split_into_chunks(text)
        total = len(chunks)

        def log(msg: str) -> None:
            if log_callback is not None:
                log_callback(msg)

        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            log(f"Using glossary: {self.config.glossary_path}")

        skill_text, skill_name = text_for_file(
            input_path, self.config.enabled_skills
        )
        if skill_name:
            log(f"Using skill: {skill_name}")

        log(f"Processing {total} chunk(s)...")

        with open(output_path, "w", encoding="utf-8") as out:
            for index, chunk in enumerate(chunks, start=1):
                if is_cancelled is not None and is_cancelled():
                    log("Translation cancelled by user.")
                    raise TranslationCancelledError("Translation was cancelled.")

                log(f"Translating chunk {index}/{total}...")

                translated = self._translate_chunk(chunk, skill_text)
                out.write(translated)
                out.write("\n\n")

                if progress_callback is not None:
                    progress_callback(index, total)

        log(f"Translation saved to: {output_path}")
