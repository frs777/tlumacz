"""Core translation logic for Tłumacz.

This module is intentionally free of Qt/CLI dependencies so it can be reused
by the GUI, future CLI versions, and installed globally as a Python package.
"""

from __future__ import annotations

import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import openai

from .cache import TranslationCache
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
from .pdf_extractor import extract_text_blocks, TextBlock

from .preprocess import (
    DEFAULT_SKIP_PATTERNS,
    protect,
    restore,
    split_segments,
    split_xml_segments,
)
from .skill import text_for_file
from .i18n import t

MAX_NODES_PER_SEGMENT = 25

# Threshold above which a chunk is considered "slow" for diagnostic purposes
# (see _log_chunk_timing). Chosen well below the 300s client timeout so a
# stuck chunk is flagged long before it would otherwise time out.
_SLOW_CHUNK_SECONDS = 30.0


def _log_chunk_timing(chunk: str, max_tokens: int, elapsed: float) -> None:
    """Append a per-chunk timing line to ~/.config/tlumacz/debug.log.

    This exists to diagnose the "translation hangs on some chunk" issue
    (see blad.md / DEBUG_QT.md item D): capping max_tokens bounds the worst
    case, but does not explain *why* a given chunk is slow. Only slow
    chunks get a short content preview, to keep the log small in the
    normal case while still giving enough to compare a future hang
    against working chunks by length, timing, and source content.

    Best-effort only: a logging failure must never break translation.
    """
    try:
        log_dir = Path.home() / ".config" / "tlumacz"
        log_dir.mkdir(parents=True, exist_ok=True)
        line = (
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"chunk_len={len(chunk)} max_tokens={max_tokens} "
            f"elapsed={elapsed:.1f}s"
        )
        if elapsed >= _SLOW_CHUNK_SECONDS:
            preview = chunk[:60].replace("\n", " ")
            line += f" SLOW preview={preview!r}"
        with open(log_dir / "debug.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


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
    parallel: int = 2
    skip_line_patterns: list[str] = field(
        default_factory=lambda: list(DEFAULT_SKIP_PATTERNS)
    )
    cache_enabled: bool = True
    cache_clear_after_translation: bool = True

    def __post_init__(self) -> None:
        base = self.system_prompt
        if not base:
            base = (
                f"You are a professional translator. "
                f"Translate ALL text into {self.target_language}. "
                f"Do not skip, omit, summarize, or shorten any content. "
                f"Every source sentence must have a corresponding translated sentence. "
                f"Return ONLY the translation — no explanations, comments, or notes."
            )
        self.system_prompt = base
        self._glossary: Glossary | None = None
        glossary_text = self._load_glossary_text()
        if glossary_text:
            base = base.rstrip() + "\n\n" + glossary_text
        self.system_prompt = base

    def _load_glossary_text(self) -> str:
        if not self.glossary_path:
            return ""
        try:
            self._glossary = Glossary.from_csv(
                self.glossary_path, max_entries=MAX_PROMPT_ENTRIES
            )
            return self._glossary.to_prompt()
        except OSError:
            self._glossary = None
            return ""

    def _glossary_prompt_for(self, source_text: str) -> str:
        """Return glossary terms that actually occur in ``source_text``.

        Filtering keeps the prompt small and prevents small models from
        echoing the whole glossary list instead of translating the source.
        """
        glossary = self._glossary
        if glossary is None or not source_text:
            return ""
        lower = source_text.casefold()
        pairs = [
            (source, target)
            for source, target in glossary.entries
            if source.casefold() != target.casefold()
            and source.casefold() in lower
        ][:MAX_PROMPT_ENTRIES]
        if not pairs:
            return ""
        lines = [f"- {source} => {target}" for source, target in pairs]
        return (
            "Use the following glossary terms exactly, do not translate them "
            "differently. Apply them ONLY to words that actually appear in "
            "the source text; never output the glossary list itself:\n"
            + "\n".join(lines)
        )


class TranslationCancelledError(Exception):
    """Raised when the user cancels a running translation."""


class Translator:
    """Translate files using an OpenAI-compatible chat completions API."""

    def __init__(self, config: TranslatorConfig) -> None:
        self.config = config
        self._cancel_event = threading.Event()
        self._client_lock = threading.Lock()
        self._active_clients: set[object] = set()
        self._cache = TranslationCache(enabled=config.cache_enabled)

    def cancel(self) -> None:
        """Interrupt active HTTP requests and prevent new translation work."""
        self._cancel_event.set()
        with self._client_lock:
            clients = list(self._active_clients)
        for client in clients:
            try:
                client.close()
            except Exception:
                pass

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

    def _build_system_prompt(self, skill_text: str = "") -> str:
        """Build the complete system prompt once per translation.

        Combines base prompt + skill + glossary into a single string
        to avoid redundant concatenation for each chunk.
        """
        system = self.config.system_prompt
        if skill_text:
            system = system.rstrip() + "\n\n" + skill_text
        # Glossary is appended if available
        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            try:
                glossary = Glossary.load(self.config.glossary_path)
            except Exception:
                glossary = None
            if glossary:
                glossary_text = glossary.prompt_snippet()
                if glossary_text:
                    system = system.rstrip() + "\n\n" + glossary_text
        return system

    def _translate_chunk(self, chunk: str, system_prompt: str) -> str:
        """Translate a single chunk via the configured API.
        
        Args:
            chunk: Text to translate.
            system_prompt: Pre-built system prompt (base + skill + glossary).
        """
        # Check cache first - avoids redundant API calls for repeated content
        cached = self._cache.get(
            chunk, system_prompt, "",
            self.config.model, self.config.temperature
        )
        if cached is not None:
            return cached

        # Translation output should be close to the source length.
        # Scale max_tokens proportionally to chunk_size - smaller chunks
        # get smaller max_tokens to avoid wasting time on token generation.
        # Multiplier 3072 accounts for target language expansion (~20-30% longer)
        # and placeholder preservation in HTML/EPUB.
        chunk_ratio = len(chunk) / max(1, self.config.chunk_size)
        max_tokens = max(256, int(3072 * chunk_ratio))
        request_kwargs: dict = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
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
            "max_tokens": max_tokens,
        }
        if self.config.chat_template_kwargs:
            request_kwargs["extra_body"] = {
                "chat_template_kwargs": self.config.chat_template_kwargs
            }
        # Tests may inject a fake client via ``translator.client``. In
        # production we create a fresh HTTP client for every chunk so a stuck
        # keep-alive connection cannot pin the single slot of a local
        # llama-server (parallel=1). Local requests are not retried.
        client = getattr(self, "client", None)
        own_client = client is None
        if own_client:
            # Local llama-server should not retry a timed-out generation:
            # the server may still be generating the abandoned request, so a
            # retry only multiplies the load and hides the real request time.
            client = openai.OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                timeout=600.0,
                max_retries=0,
            )
        if self._cancel_event.is_set():
            if own_client:
                client.close()
            raise TranslationCancelledError(t("log.translation_cancelled"))
        with self._client_lock:
            self._active_clients.add(client)
        request_start = time.monotonic()
        try:
            response = client.chat.completions.create(**request_kwargs)
            if self._cancel_event.is_set():
                raise TranslationCancelledError(t("log.translation_cancelled"))
            content = response.choices[0].message.content or ""
        except TranslationCancelledError:
            raise
        except Exception:
            if self._cancel_event.is_set():
                raise TranslationCancelledError(t("log.translation_cancelled"))
            raise
        finally:
            _log_chunk_timing(chunk, max_tokens, time.monotonic() - request_start)
            with self._client_lock:
                self._active_clients.discard(client)
                try:
                    client.close()
                except Exception:
                    pass
        result = _strip_eos_tokens(content)
        # Store in cache for future use
        self._cache.put(
            chunk, system_prompt, "",
            self.config.model, self.config.temperature, result
        )
        return result

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
            log(t("log.extracting_text", ext=ext))
            
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
            # PDF: tłumacz tekst z zachowaniem układu (PyMuPDF, bez OCR)
            if ext == "pdf":
                return self._translate_pdf(
                    input_path, output_path,
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
            log(t("log.using_glossary", path=self.config.glossary_path))

        if skill_name:
            log(t("log.using_skill", name=skill_name))

        # Build system prompt once for all chunks
        system_prompt = self._build_system_prompt(skill_text)

        if protected:
            log(t("log.protected_fragments", count=len(protected)))
        log(t("log.processing_blocks", count=total))

        with open(output_path, "w", encoding="utf-8") as out:
            written = 0
            translate_segments = [(i, content) for i, (kind, content) in enumerate(segments) if kind == "translate"]
            translated_map: dict[int, str] = {}
            if self.config.parallel > 1 and len(translate_segments) > 1:
                executor = ThreadPoolExecutor(max_workers=self.config.parallel)
                try:
                    futures = {executor.submit(self._translate_chunk, content, system_prompt): i for i, content in translate_segments}
                    done_count = 0
                    for future in as_completed(futures):
                        if is_cancelled is not None and is_cancelled():
                            raise TranslationCancelledError(t("log.translation_cancelled"))
                        translated_map[futures[future]] = future.result()
                        done_count += 1
                        if progress_callback is not None:
                            progress_callback(done_count, len(translate_segments))
                except TranslationCancelledError:
                    self.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                executor.shutdown(wait=True)
            for index, (kind, content) in enumerate(segments):
                if is_cancelled is not None and is_cancelled():
                    log(t("log.translation_cancelled"))
                    raise TranslationCancelledError(t("log.translation_cancelled"))

                if kind == "keep":
                    out.write(content)
                    out.write("\n")
                    continue

                written += 1
                log(t("log.translating_block", current=written, total=total))

                translated = translated_map[index] if translated_map else self._translate_chunk(content, system_prompt)
                out.write(restore(translated, protected))
                out.write("\n\n")

                if progress_callback is not None:
                    progress_callback(written, total)

        log(t("log.translation_saved", path=output_path))

        # Log cache statistics
        cache_stats = self._cache.stats()
        if cache_stats.get("enabled"):
            hits = cache_stats["hits"]
            misses = cache_stats["misses"]
            total_requests = hits + misses
            if total_requests > 0:
                effectiveness = (hits / total_requests) * 100
                log(t("log.buffer_stats", hits=hits, misses=misses, effectiveness=f"{effectiveness:.0f}"))
            else:
                log(t("log.buffer_no_lookups"))
        
        # Clear cache after translation if configured (for accurate benchmarking)
        if self.config.cache_clear_after_translation:
            self._cache.clear()
            log(t("log.buffer_cleared"))
        
        self._cache.reset_stats()

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

        _log(t("log.extracting_epub"))
        try:
            structure = extract_epub_structure(input_path)
        except ExtractionError as exc:
            raise ExtractionError(f"Nie można przetłumaczyć pliku EPUB: {exc}") from exc

        files = structure["files"]
        xhtml_paths = structure["xhtml_paths"]
        _log(t("log.found_xhtml_files", count=len(xhtml_paths)))

        skill_text, skill_name, _ = text_for_file(
            input_path, self.config.enabled_skills
        )
        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            _log(t("log.using_glossary", path=self.config.glossary_path))
        if skill_name:
            _log(t("log.using_skill", name=skill_name))

        # Build system prompt once for all XHTML files
        system_prompt = self._build_system_prompt(skill_text)

        updates: dict[str, bytes] = {}
        for idx, rel in enumerate(xhtml_paths, start=1):
            raw = files[rel].decode("utf-8", errors="replace")
            _log(t("log.translating_file", current=idx, total=len(xhtml_paths), name=rel))
            translated_html = self._translate_xhtml_inplace(
                raw, system_prompt,
                log=_log, progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )
            updates[rel] = translated_html.encode("utf-8")

        _log(t("log.building_epub"))
        try:
            reconstruct_epub(files, updates, output_path)
        except Exception as exc:  # noqa: BLE001
            raise ExtractionError(f"Błąd przy budowaniu EPUB: {exc}") from exc
        _log(t("log.epub_saved", path=output_path))

        # Log cache statistics
        cache_stats = self._cache.stats()
        if cache_stats.get("enabled"):
            hits = cache_stats["hits"]
            misses = cache_stats["misses"]
            total_requests = hits + misses
            if total_requests > 0:
                effectiveness = (hits / total_requests) * 100
                _log(t("log.buffer_stats", hits=hits, misses=misses, effectiveness=f"{effectiveness:.0f}"))
            else:
                _log(t("log.buffer_no_lookups"))

        # Clear cache after translation if configured
        if self.config.cache_clear_after_translation:
            self._cache.clear()
            _log(t("log.buffer_cleared_short"))

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

        _log(t("log.unpacking_archive", ext=ext))
        try:
            structure = extract_office_structure(input_path, ext)
        except ExtractionError as exc:
            raise ExtractionError(
                f"Nie można przetłumaczyć pliku .{ext}: {exc}"
            ) from exc

        files = structure["files"]
        content_paths = structure["content_paths"]
        _log(t("log.found_content_files", count=len(content_paths)))

        skill_text, skill_name, _ = text_for_file(
            input_path, self.config.enabled_skills
        )
        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            _log(t("log.using_glossary", path=self.config.glossary_path))
        if skill_name:
            _log(t("log.using_skill", name=skill_name))

        # Build system prompt once for all XML files
        system_prompt = self._build_system_prompt(skill_text)

        updates: dict[str, bytes] = {}
        for idx, rel in enumerate(content_paths, start=1):
            raw = files[rel].decode("utf-8", errors="replace")
            _log(t("log.translating_file", current=idx, total=len(content_paths), name=rel))
            translated = self._translate_document_xml(
                raw, ext, system_prompt,
                log=_log, progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )
            updates[rel] = translated.encode("utf-8")

        _log(t("log.building_archive", format=label))
        try:
            reconstruct_zip(files, updates, output_path)
        except Exception as exc:  # noqa: BLE001
            raise ExtractionError(f"Błąd przy budowaniu {label}: {exc}") from exc
        _log(t("log.archive_saved", format=label, path=output_path))

        # Log cache statistics
        cache_stats = self._cache.stats()
        if cache_stats.get("enabled"):
            hits = cache_stats["hits"]
            misses = cache_stats["misses"]
            total_requests = hits + misses
            if total_requests > 0:
                effectiveness = (hits / total_requests) * 100
                _log(t("log.buffer_stats", hits=hits, misses=misses, effectiveness=f"{effectiveness:.0f}"))
            else:
                _log(t("log.buffer_no_lookups"))

        # Clear cache after translation if configured
        if self.config.cache_clear_after_translation:
            self._cache.clear()
            _log(t("log.buffer_cleared_short"))

        return output_path

    def _translate_pdf(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
        log: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Tłumaczy PDF z zachowaniem układu (tekstowe, bez OCR).

        Ekstrahuje bloki tekstu z pozycjami za pomocą PyMuPDF, tłumaczy tekst,
        a następnie wstawia przetłumaczony tekst z powrotem do PDF w oryginalnych
        pozycjach z zachowaniem rozmiaru czcionki. Obrazki i inne elementy
        nietekstowe są zachowywane.
        """
        import fitz  # PyMuPDF

        def _log(msg: str) -> None:
            if log:
                log(msg)

        _log(t("log.extracting_pdf"))
        try:
            blocks = extract_text_blocks(input_path)
        except Exception as exc:
            raise ExtractionError(f"Nie można przetłumaczyć pliku PDF: {exc}") from exc

        if not blocks:
            raise ExtractionError("Plik PDF nie zawiera tekstu do przetłumaczenia.")

        _log(t("log.found_text_blocks", count=len(blocks)))

        skill_text, skill_name, _ = text_for_file(
            input_path, self.config.enabled_skills
        )
        if self.config.glossary_path and os.path.exists(self.config.glossary_path):
            _log(t("log.using_glossary", path=self.config.glossary_path))
        if skill_name:
            _log(t("log.using_skill", name=skill_name))

        system_prompt = self._build_system_prompt(skill_text)

        # Otwórz PDF do edycji
        doc = fitz.open(input_path)

        # Tłumacz każdy blok i wstawiaj z powrotem do PDF
        total_blocks = len(blocks)
        for idx, block in enumerate(blocks):
            if is_cancelled is not None and is_cancelled():
                _log(t("log.translation_cancelled"))
                doc.close()
                raise TranslationCancelledError(t("log.translation_cancelled"))

            _log(t("log.translating_block", current=idx + 1, total=total_blocks))

            # Tłumacz tekst bloku
            original_text = block.text
            translated_text = self._translate_chunk(original_text, system_prompt)

            # Wstaw przetłumaczony tekst z powrotem do PDF
            page = doc[block.page_num]

            # Prostokąt bloku
            rect = fitz.Rect(block.x0, block.y0, block.x1, block.y1)

            # Usuń oryginalny tekst (redact)
            page.add_redact_annot(rect)
            page.apply_redactions()

            # Wstaw przetłumaczony tekst
            # Użyj rozmiaru czcionki z pierwszego spana
            font_size = block.spans[0].font_size if block.spans else 11.0

            # Ścieżka do czcionki TrueType z obsługą Unicode (polskie znaki)
            font_path = "/usr/share/fonts/noto/NotoSans-Regular.ttf"
            font_name = "NotoSans"

            # Dodaj czcionkę do strony (wymagane dla Unicode)
            page.insert_font(fontname=font_name, fontfile=font_path)

            # Spróbuj wstawić tekst z oryginalnym rozmiarem czcionki
            rc = page.insert_textbox(
                rect,
                translated_text,
                fontsize=font_size,
                fontname=font_name,
                align=0,  # wyrównanie do lewej
            )

            # Jeśli tekst nie mieści się, zmniejsz rozmiar czcionki
            if rc < 0:
                scale_factor = 0.9
                new_font_size = font_size * scale_factor
                _log(t("log.text_not_fitting", from_size=font_size, to_size=new_font_size))

                rc = page.insert_textbox(
                    rect,
                    translated_text,
                    fontsize=new_font_size,
                    fontname=font_name,
                    align=0,
                )

                if rc < 0:
                    new_font_size = font_size * 0.7
                    _log(t("log.still_not_fitting", size=new_font_size))
                    rc = page.insert_textbox(
                        rect,
                        translated_text,
                        fontsize=new_font_size,
                        fontname=font_name,
                        align=0,
                    )

            if rc < 0:
                _log(t("log.text_may_be_truncated", block_num=idx + 1))

            if progress_callback is not None:
                progress_callback(idx + 1, total_blocks)

        # Zapisz przetłumaczony PDF
        _log(t("log.saving_pdf"))
        doc.save(output_path)
        doc.close()

        _log(t("log.pdf_saved", path=output_path))

        # Log cache statistics
        cache_stats = self._cache.stats()
        if cache_stats.get("enabled"):
            hits = cache_stats["hits"]
            misses = cache_stats["misses"]
            total_requests = hits + misses
            if total_requests > 0:
                effectiveness = (hits / total_requests) * 100
                _log(t("log.buffer_stats", hits=hits, misses=misses, effectiveness=f"{effectiveness:.0f}"))
            else:
                _log(t("log.buffer_no_lookups"))

        # Clear cache after translation if configured
        if self.config.cache_clear_after_translation:
            self._cache.clear()
            _log(t("log.buffer_cleared_short"))

        return output_path

    def _translate_document_xml(
        self,
        raw_xml: str,
        ext: str,
        system_prompt: str,
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
                if is_text and elem.text and elem.text.strip():
                    slots.append((elem, "text"))
            else:
                # ODT: tekst może być w .text lub .tail zagnieżdżonych elementów
                is_text = elem.tag.startswith(text_ns)
                if is_text:
                    if elem.text and elem.text.strip():
                        slots.append((elem, "text"))
                    if elem.tail and elem.tail.strip():
                        slots.append((elem, "tail"))

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

        slot_texts = [
            elem.text if kind == "text" else elem.tail
            for elem, kind in slots
        ]
        total = 0
        for idx, (elem, kind) in enumerate(slots):
            total += len(elem.text if kind == "text" else elem.tail or "")

        segments: list[list[int]] = []
        current: list[int] = []
        current_len = 0
        for idx in range(len(slots)):
            elem, kind = slots[idx]
            txt = elem.text if kind == "text" else elem.tail or ""
            too_many = len(current) >= MAX_NODES_PER_SEGMENT
            if current and (
                too_many or current_len + len(txt) + 8 > self.config.chunk_size
            ):
                segments.append(current)
                current, current_len = [], 0
            current.append(idx)
            current_len += len(txt) + 8

        if current:
            segments.append(current)

        for seg_idx, seg in enumerate(segments):
            if is_cancelled is not None and is_cancelled():
                log(t("log.translation_cancelled"))
                raise TranslationCancelledError(t("log.translation_cancelled"))
            texts = [
                slots[i][0].text if slots[i][1] == "text" else slots[i][0].tail or ""
                for i in seg
            ]
            joined = texts[0]
            for j, text in enumerate(texts[1:], 1):
                joined += f"\n⟦S_{j-1}⟧\n" + text
            log(t("log.translating_segment", current=seg_idx + 1, total=len(segments)))
            translated = self._translate_chunk(joined, system_prompt)
            parts = re.split(r"⟦S_\d+⟧", translated)
            if len(parts) == len(seg):
                for i, chunk_i in zip(seg, parts):
                    elem, kind = slots[i]
                    if kind == "text":
                        elem.text = chunk_i
                    else:
                        elem.tail = chunk_i
            else:
                # Model dropped/mangled separators: translate each node alone.
                for i in seg:
                    if is_cancelled is not None and is_cancelled():
                        raise TranslationCancelledError(
                            t("log.translation_cancelled")
                        )
                    elem, kind = slots[i]
                    text = elem.text if kind == "text" else elem.tail or ""
                    translated_node = self._translate_chunk(text, system_prompt)
                    if kind == "text":
                        elem.text = translated_node
                    else:
                        elem.tail = translated_node
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

    def _translate_xhtml_inplace(
        self,
        raw_xhtml: str,
        system_prompt: str,
        *,
        log: Callable[[str], None],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Translate XHTML content in place, preserving all tags.

        Similar to _translate_document_xml but for arbitrary XHTML.
        Iterates over all elements and translates .text and .tail in place.
        """
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(raw_xhtml)
        except ET.ParseError:
            return self._translate_text(
                raw_xhtml, "", [],
                log=log, progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )

        # Zbierz wszystkie sloty tekstowe (text i tail)
        slots: list[tuple[object, str]] = []
        for elem in root.iter():
            # Pomijamy elementy które nie powinny być tłumaczone
            # Tag może mieć namespace, więc bierzemy tylko lokalną nazwę
            tag = elem.tag.split("}")[-1].lower() if isinstance(elem.tag, str) and "}" in elem.tag else (elem.tag.lower() if isinstance(elem.tag, str) else "")
            if tag in ("script", "style", "head", "meta", "link", "title"):
                continue
            if elem.text and elem.text.strip():
                slots.append((elem, "text"))
            if elem.tail and elem.tail.strip():
                slots.append((elem, "tail"))

        if not slots:
            return raw_xhtml

        # Zachowaj deklarację XML i namespace'y
        declaration = ""
        if raw_xhtml.lstrip().startswith("<?xml"):
            start = raw_xhtml.find("<?xml")
            declaration = raw_xhtml[start : raw_xhtml.find("?>", start) + 2]

        orig_ns: list[tuple[str, str]] = [
            (m.group(1) or "", m.group(2))
            for m in re.finditer(r'xmlns(?::([a-zA-Z0-9_]+))?="([^"]+)"', raw_xhtml)
        ]
        for prefix, uri in orig_ns:
            ET.register_namespace(prefix, uri)

        # Podziel na segmenty
        segments: list[list[int]] = []
        current: list[int] = []
        current_len = 0
        for idx in range(len(slots)):
            elem, kind = slots[idx]
            txt = elem.text if kind == "text" else elem.tail or ""
            too_many = len(current) >= MAX_NODES_PER_SEGMENT
            if current and (
                too_many or current_len + len(txt) + 8 > self.config.chunk_size
            ):
                segments.append(current)
                current, current_len = [], 0
            current.append(idx)
            current_len += len(txt) + 8

        if current:
            segments.append(current)

        for seg_idx, seg in enumerate(segments):
            if is_cancelled is not None and is_cancelled():
                log(t("log.translation_cancelled"))
                raise TranslationCancelledError(t("log.translation_cancelled"))
            texts = [
                slots[i][0].text if slots[i][1] == "text" else slots[i][0].tail or ""
                for i in seg
            ]
            joined = texts[0]
            for j, text in enumerate(texts[1:], 1):
                joined += f"\n⟦S_{j-1}⟧\n" + text
            log(t("log.translating_segment", current=seg_idx + 1, total=len(segments)))
            translated = self._translate_chunk(joined, system_prompt)
            parts = re.split(r"⟦S_\d+⟧", translated)
            if len(parts) == len(seg):
                for i, chunk_i in zip(seg, parts):
                    elem, kind = slots[i]
                    if kind == "text":
                        elem.text = chunk_i
                    else:
                        elem.tail = chunk_i
            else:
                for i in seg:
                    if is_cancelled is not None and is_cancelled():
                        raise TranslationCancelledError(t("log.translation_cancelled"))
                    elem, kind = slots[i]
                    text = elem.text if kind == "text" else elem.tail or ""
                    translated_node = self._translate_chunk(text, system_prompt)
                    if kind == "text":
                        elem.text = translated_node
                    else:
                        elem.tail = translated_node
            if progress_callback is not None:
                progress_callback(seg_idx + 1, len(segments))

        body = ET.tostring(root, encoding="unicode", xml_declaration=False)

        # Przywróć namespace'y
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
            log(t("log.no_text_to_translate"))
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

        # Build system prompt once for all chunks
        system_prompt = self._build_system_prompt(skill_text)

        if protected:
            log(t("log.protected_fragments", count=len(protected)))
        log(t("log.processing_blocks", count=total))

        parts: list[str] = []
        written = 0
        for kind, content in segments:
            if is_cancelled is not None and is_cancelled():
                log(t("log.translation_cancelled"))
                raise TranslationCancelledError(t("log.translation_cancelled"))

            if kind == "keep":
                parts.append(content + "\n")
                continue

            written += 1
            log(f"Tłumaczenie bloku {written}/{total}...")
            translated = self._translate_chunk(content, system_prompt)
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


_EOS_TOKEN_RE = re.compile(
    r"<\|im_end\|>?|<\|end_of_turn\|>?|<\|eot_id\|>?|<\|file_separator\|>|</s>"
)
_START_TOKEN_RE = re.compile(r"<\|im_start\|>?")


def _strip_eos_tokens(content: str) -> str:
    """Remove chat-template control tokens leaked into the output.

    Some models (e.g. chatml templates) emit their control tokens (``<|im_end|>``,
    ``<|im_start|>``, ``</s>``, ...) even in the middle of a response, sometimes
    truncated (e.g. ``<|im_start`` without closing ``|>``). They must not land
    in the output file.
    """
    content = _START_TOKEN_RE.sub("", content)
    content = _EOS_TOKEN_RE.sub("", content)
    return content
