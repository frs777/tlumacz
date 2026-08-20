"""Core translation logic for Tłumacz.

This module is intentionally free of Qt/CLI dependencies so it can be reused
by the GUI, future CLI versions, and installed globally as a Python package.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import openai

from .extract import (
    ExtractionError,
    extract_epub_structure,
    extract_office_structure,
    extract_text,
    is_binary_format,
    reconstruct_epub,
    reconstruct_zip,
)
from .glossary import Glossary, MAX_PROMPT_ENTRIES
from .preprocess import (
    DEFAULT_SKIP_PATTERNS,
    protect,
    restore,
    split_segments,
    split_xml_segments,
)
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
    chat_template_kwargs: Optional[dict] = None
    skip_line_patterns: list[str] = field(
        default_factory=lambda: list(DEFAULT_SKIP_PATTERNS)
    )

    def __post_init__(self) -> None:
        base = self.system_prompt
        if base is None:
            base = (
                "You are a professional technical translator. "
                "The text may be written in more than one language. "
                f"Translate ALL passages that are not already in "
                f"{self.target_language} into {self.target_language}, "
                "preserving Markdown formatting. Every sentence in another "
                "language (for example English, German, French) must be "
                "translated - do not skip, omit, or leave any passage in its "
                "original language. Passages that are already in "
                f"{self.target_language} must be returned unchanged. "
                "Respond directly with the translation only. Do not include "
                "any thinking, reasoning, or commentary."
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
        request_kwargs: dict = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        f"Translate ALL passages of the following text that "
                        f"are not already in {self.config.target_language} into "
                        f"{self.config.target_language}, preserving Markdown "
                        "formatting. Do not leave any passage in another "
                        "language - every foreign-language sentence must be "
                        "translated:\n\n"
                        f"{chunk}"
                    ),
                },
            ],
            "temperature": self.config.temperature,
            "max_tokens": 6000,
        }
        if self.config.chat_template_kwargs:
            request_kwargs["extra_body"] = {
                "chat_template_kwargs": self.config.chat_template_kwargs
            }
        response = self.client.chat.completions.create(**request_kwargs)
        content = response.choices[0].message.content or ""
        return _strip_eos_tokens(content)

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

        def log(msg: str) -> None:
            if log_callback is not None:
                log_callback(msg)

        if is_binary_format(input_path):
            ext = Path(input_path).suffix.lower().lstrip(".")
            log(f"Wyodrębnianie tekstu z pliku .{ext}...")
            
            # Specjalna ścieżka dla EPUB - bezpośrednio na XHTML, bez Markdowna
            if ext == "epub":
                return self._translate_epub_xhtml(
                    input_path, output_path,
                    progress_callback, log_callback, is_cancelled, log
                )
            # DOCX/ODT: tłumacz XML wewnątrz archiwum, aby zachować format 1:1
            if ext in ("docx", "odt"):
                return self._translate_office_zip(
                    input_path, output_path, ext,
                    progress_callback, log_callback, is_cancelled, log
                )
            
            try:
                text = extract_text(input_path)
            except ExtractionError as exc:
                raise ExtractionError(
                    f"Nie można przetłumaczyć pliku .{ext}: {exc}"
                ) from exc
            if not text.strip():
                raise ExtractionError(
                    f"Plik .{ext} nie zawiera tekstu do przetłumaczenia."
                )
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                text = f.read()

        masked, protected = protect(text)
        skill_text, skill_name, skill_patterns = text_for_file(
            input_path, self.config.enabled_skills
        )
        segments = split_segments(
            masked,
            self.config.chunk_size,
            self._effective_skip_patterns(skill_patterns),
        )
        total = sum(1 for kind, _ in segments if kind == "translate")

        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            log(f"Using glossary: {self.config.glossary_path}")

        if skill_name:
            log(f"Using skill: {skill_name}")

        if protected:
            log(f"Protected {len(protected)} code/URL fragment(s)")
        log(f"Processing {total} chunk(s)...")

        with open(output_path, "w", encoding="utf-8") as out:
            written = 0
            for kind, content in segments:
                if is_cancelled is not None and is_cancelled():
                    log("Translation cancelled by user.")
                    raise TranslationCancelledError("Translation was cancelled.")

                if kind == "keep":
                    out.write(content)
                    out.write("\n")
                    continue

                written += 1
                log(f"Translating chunk {written}/{total}...")

                translated = self._translate_chunk(content, skill_text)
                out.write(restore(translated, protected))
                out.write("\n\n")

                if progress_callback is not None:
                    progress_callback(written, total)

        log(f"Translation saved to: {output_path}")

    def _translate_epub_xhtml(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
        log: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Translate an EPUB by processing each XHTML file and rebuilding it.

        The raw XHTML of every content file is fed through the standard text
        pipeline (protect -> split -> translate -> restore), so the HTML
        structure and tags are preserved by the model while only the visible
        text is translated. All non-content files (CSS, images, fonts, OPF,
        NCX, mimetype, META-INF) are copied verbatim.
        """
        def _log(msg: str) -> None:
            if log:
                log(msg)

        _log("Wyodrębnianie struktury z EPUB...")
        try:
            structure = extract_epub_structure(input_path)
        except ExtractionError as exc:
            raise ExtractionError(f"Nie można przetłumaczyć pliku EPUB: {exc}") from exc

        files = structure["files"]
        xhtml_paths = structure["xhtml_paths"]
        _log(f"Znaleziono {len(xhtml_paths)} plik(ów) treści do przetłumaczenia.")

        skill_text, skill_name, _ = text_for_file(
            input_path, self.config.enabled_skills
        )
        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            _log(f"Using glossary: {self.config.glossary_path}")
        if skill_name:
            _log(f"Using skill: {skill_name}")

        updates: dict[str, bytes] = {}
        for idx, rel in enumerate(xhtml_paths, start=1):
            raw = files[rel].decode("utf-8", errors="replace")
            _log(f"Tłumaczenie pliku {idx}/{len(xhtml_paths)}: {rel}")
            translated_html = self._translate_text(
                raw, skill_text, [],
                log=_log, progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )
            updates[rel] = translated_html.encode("utf-8")

        _log("Budowanie przetłumaczonego EPUB...")
        try:
            reconstruct_epub(files, updates, output_path)
        except Exception as exc:  # noqa: BLE001
            raise ExtractionError(f"Błąd przy budowaniu EPUB: {exc}") from exc
        _log(f"Zapisano przetłumaczony EPUB: {output_path}")
        return output_path

    def _translate_office_zip(
        self,
        input_path: str,
        output_path: str,
        ext: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
        log: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Translate a DOCX/ODT in place, preserving the original structure 1:1.

        The archive is unpacked; every content XML file (word/document.xml,
        headers/footers, content.xml, ...) has its text nodes translated in
        place via :meth:`_translate_document_xml` — only the visible text is
        sent to the model, the XML markup itself never is, so the document
        structure, styles and tables survive exactly as they were. All other
        files (styles, media, rels) are copied verbatim and the archive is
        rebuilt.
        """
        label = "ODT" if ext == "odt" else "DOCX"

        def _log(msg: str) -> None:
            if log:
                log(msg)

        _log(f"Rozpakowywanie pliku .{ext}...")
        try:
            structure = extract_office_structure(input_path, ext)
        except ExtractionError as exc:
            raise ExtractionError(
                f"Nie można przetłumaczyć pliku .{ext}: {exc}"
            ) from exc

        files = structure["files"]
        content_paths = structure["content_paths"]
        _log(
            f"Znaleziono {len(content_paths)} plik(ów) treści do przetłumaczenia."
        )

        skill_text, skill_name, _ = text_for_file(
            input_path, self.config.enabled_skills
        )
        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            _log(f"Using glossary: {self.config.glossary_path}")
        if skill_name:
            _log(f"Using skill: {skill_name}")

        updates: dict[str, bytes] = {}
        for idx, rel in enumerate(content_paths, start=1):
            raw = files[rel].decode("utf-8", errors="replace")
            _log(f"Tłumaczenie pliku {idx}/{len(content_paths)}: {rel}")
            translated = self._translate_document_xml(
                raw, ext,
                log=_log, progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )
            updates[rel] = translated.encode("utf-8")

        _log(f"Budowanie przetłumaczonego pliku {label}...")
        try:
            reconstruct_zip(files, updates, output_path)
        except Exception as exc:  # noqa: BLE001
            raise ExtractionError(f"Błąd przy budowaniu {label}: {exc}") from exc
        _log(f"Zapisano przetłumaczony {label}: {output_path}")
        return output_path

    def _translate_document_xml(
        self,
        raw_xml: str,
        ext: str,
        *,
        log: Callable[[str], None],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Translate the text of an XML document in place, markup untouched.

        Only the ``.text`` of text-bearing nodes (``w:t`` for DOCX, ``text:*``
        elements for ODT) is extracted, translated through the configured model,
        and written back into the same tree. Because the markup is never sent
        to the model, the structure, styles and empty elements are preserved
        exactly — ideal for administrative documents.
        """
        import xml.etree.ElementTree as ET

        if ext == "docx":
            text_tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
        else:
            text_ns = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"

        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError:
            # Not well-formed XML; fall back to the generic text pipeline.
            return self._translate_text(
                raw_xml, "", [],
                log=log, progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )

        slots: list[tuple[object, str]] = []
        for elem in root.iter():
            if ext == "docx":
                is_text = elem.tag == text_tag
            else:
                is_text = elem.tag.startswith(text_ns)
            if is_text and elem.text and elem.text.strip():
                slots.append((elem, "text"))

        if not slots:
            return raw_xml

        # Keep the original XML declaration.
        declaration = ""
        if raw_xml.lstrip().startswith("<?xml"):
            start = raw_xml.find("<?xml")
            declaration = raw_xml[start : raw_xml.find("?>", start) + 2]

        # Keep the original namespace prefixes (w:, text:, office:, ...).
        orig_ns: list[tuple[str, str]] = [
            (m.group(1) or "", m.group(2))
            for m in re.finditer(r'xmlns(?::([a-zA-Z0-9_]+))?="([^"]+)"', raw_xml)
        ]
        for prefix, uri in orig_ns:
            ET.register_namespace(prefix, uri)

        slot_texts = [elem.text for elem, _ in slots]
        total = 0
        for idx, elem in enumerate(slots):
            total += len(elem[0].text or "")

        segments: list[list[int]] = []
        current: list[int] = []
        current_len = 0
        for idx in range(len(slots)):
            t = slots[idx][0].text or ""
            if current and current_len + len(t) + 8 > self.config.chunk_size:
                segments.append(current)
                current, current_len = [], 0
            current.append(idx)
            current_len += len(t) + 8

        if current:
            segments.append(current)

        for seg_idx, seg in enumerate(segments):
            if is_cancelled is not None and is_cancelled():
                log("Translation cancelled by user.")
                raise TranslationCancelledError("Translation was cancelled.")
            marker = "\n⟦S_%d⟧\n"
            joined = marker.join(slots[i][0].text or "" for i in seg)
            log(f"Tłumaczenie segmentu {seg_idx + 1}/{len(segments)}...")
            translated = self._translate_chunk(joined, "")
            parts = re.split(r"⟦S_\d+⟧", translated)
            if len(parts) == len(seg) + 1:
                for i, chunk_i in zip(seg, parts[1:]):
                    slots[i][0].text = chunk_i
            else:
                # Model dropped/mangled separators: translate each node alone.
                for i in seg:
                    if is_cancelled is not None and is_cancelled():
                        raise TranslationCancelledError(
                            "Translation was cancelled."
                        )
                    slots[i][0].text = self._translate_chunk(slots[i][0].text or "", "")
            if progress_callback is not None:
                progress_callback(seg_idx + 1, len(segments))

        body = ET.tostring(root, encoding="unicode", xml_declaration=False)

        # ET omits xmlns declarations that are unused by the tree; re-add the
        # ones present in the original so the document stays structurally intact.
        missing = []
        for prefix, uri in orig_ns:
            key = f'xmlns:{prefix}="' if prefix else 'xmlns="'
            if key not in body:
                missing.append(f' xmlns:{prefix}="{uri}"' if prefix else f' xmlns="{uri}"')
        if missing:
            root_open = body.find(">")
            body = body[:root_open] + "".join(missing) + body[root_open:]

        return declaration + body

    def _translate_text(
        self,
        text: str,
        skill_text: str,
        skip_patterns: list[str],
        *,
        log: Callable[[str], None],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Run the protect -> split -> translate -> restore pipeline over ``text``.

        Returns the fully translated text as a single string.
        """
        masked, protected = protect(text)
        if not re.sub(r"⟦PROT_\d+⟧|\s", "", masked):
            log("Brak tekstu do przetłumaczenia - kopiuję plik bez zmian.")
            return text
        if protected:
            segments = split_xml_segments(masked, self.config.chunk_size)
        else:
            segments = split_segments(
                masked,
                self.config.chunk_size,
                skip_patterns,
            )
        total = sum(1 for kind, _ in segments if kind == "translate")

        if protected:
            log(f"Protected {len(protected)} code/URL fragment(s)")
        log(f"Processing {total} chunk(s)...")

        parts: list[str] = []
        written = 0
        for kind, content in segments:
            if is_cancelled is not None and is_cancelled():
                log("Translation cancelled by user.")
                raise TranslationCancelledError("Translation was cancelled.")

            if kind == "keep":
                parts.append(content + "\n")
                continue

            written += 1
            log(f"Translating chunk {written}/{total}...")
            translated = self._translate_chunk(content, skill_text)
            parts.append(restore(translated, protected) + "\n\n")

            if progress_callback is not None:
                progress_callback(written, total)

        return "".join(parts)

    def _effective_skip_patterns(self, skill_patterns: tuple[str, ...]) -> list[str]:
        """Combine skill patterns, defaults and the user's custom patterns.

        The matched skill's patterns (or the generic defaults when the skill
        does not define any) form the base; the user's ``skip_line_patterns``
        are appended, deduplicated, so custom rules always win.
        """
        patterns = list(skill_patterns or DEFAULT_SKIP_PATTERNS)
        for pattern in self.config.skip_line_patterns:
            if pattern not in patterns:
                patterns.append(pattern)
        return patterns


_EOS_TOKEN_RE = re.compile(r"(<\|im_end\|>|<\|end_of_turn\|>|<\|eot_id\|>|</s>)\s*$")
_START_TOKEN_RE = re.compile(r"\s*<\|im_start\|>")


def _strip_eos_tokens(content: str) -> str:
    """Remove chat-template control tokens leaked into the output.

    Some models (e.g. chatml templates) emit their control tokens (``<|im_end|>``,
    ``<|im_start|>``, ``</s>``, ...) at the end of a response even though they
    are not part of the translation. They must not land in the output file.
    """
    content = _START_TOKEN_RE.sub("", content)
    return _EOS_TOKEN_RE.sub("", content)
