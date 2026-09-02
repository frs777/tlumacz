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
from .preprocess import (
    DEFAULT_SKIP_PATTERNS,
    protect,
    restore,
    split_segments,
    split_xml_segments,
)
from .skill import text_for_file

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
    parallel: int = 1
    skip_line_patterns: list[str] = field(
        default_factory=lambda: list(DEFAULT_SKIP_PATTERNS)
    )
    cache_enabled: bool = True
    cache_clear_after_translation: bool = True

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
        system = self.config.system_prompt or DEFAULT_SYSTEM_PROMPT
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
        chunk_ratio = len(chunk) / max(1, self.config.chunk_size)
        max_tokens = max(256, int(1024 * chunk_ratio))
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
                timeout=300.0,
                max_retries=0,
            )
        if self._cancel_event.is_set():
            if own_client:
                client.close()
            raise TranslationCancelledError("Translation was cancelled.")
        with self._client_lock:
            self._active_clients.add(client)
        request_start = time.monotonic()
        try:
            response = client.chat.completions.create(**request_kwargs)
            if self._cancel_event.is_set():
                raise TranslationCancelledError("Translation was cancelled.")
            content = response.choices[0].message.content or ""
        except TranslationCancelledError:
            raise
        except Exception:
            if self._cancel_event.is_set():
                raise TranslationCancelledError("Translation was cancelled.")
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

        # Build system prompt once for all chunks
        system_prompt = self._build_system_prompt(skill_text)

        if protected:
            log(f"Protected {len(protected)} code/URL fragment(s)")
        log(f"Processing {total} chunk(s)...")

        with open(output_path, "w", encoding="utf-8") as out:
            written = 0
            translate_segments = [(i, content) for i, (kind, content) in enumerate(segments) if kind == "translate"]
            translated_map: dict[int, str] = {}
            if self.config.parallel > 1 and len(translate_segments) > 1:
                executor = ThreadPoolExecutor(max_workers=self.config.parallel)
                try:
                    futures = {executor.submit(self._translate_chunk, content, system_prompt): i for i, content in translate_segments}
                    for future in as_completed(futures):
                        if is_cancelled is not None and is_cancelled():
                            raise TranslationCancelledError("Translation was cancelled.")
                        translated_map[futures[future]] = future.result()
                except TranslationCancelledError:
                    self.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                executor.shutdown(wait=True)
            for index, (kind, content) in enumerate(segments):
                if is_cancelled is not None and is_cancelled():
                    log("Translation cancelled by user.")
                    raise TranslationCancelledError("Translation was cancelled.")

                if kind == "keep":
                    out.write(content)
                    out.write("\n")
                    continue

                written += 1
                log(f"Translating chunk {written}/{total}...")

                translated = translated_map[index] if translated_map else self._translate_chunk(content, system_prompt)
                out.write(restore(translated, protected))
                out.write("\n\n")

                if progress_callback is not None:
                    progress_callback(written, total)

        log(f"Translation saved to: {output_path}")

        # Log cache statistics
        cache_stats = self._cache.stats()
        if cache_stats.get("enabled"):
            hits = cache_stats["hits"]
            misses = cache_stats["misses"]
            total_requests = hits + misses
            if total_requests > 0:
                effectiveness = (hits / total_requests) * 100
                log(f"Cache: {hits} hits, {misses} misses ({effectiveness:.0f}% effectiveness)")
            else:
                log("Cache: no lookups")
        
        # Clear cache after translation if configured (for accurate benchmarking)
        if self.config.cache_clear_after_translation:
            self._cache.clear()
            log("Cache cleared after translation")
        
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

        # Build system prompt once for all XML files
        system_prompt = self._build_system_prompt(skill_text)

        updates: dict[str, bytes] = {}
        for idx, rel in enumerate(content_paths, start=1):
            raw = files[rel].decode("utf-8", errors="replace")
            _log(f"Tłumaczenie pliku {idx}/{len(content_paths)}: {rel}")
            translated = self._translate_document_xml(
                raw, ext, system_prompt,
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
            too_many = len(current) >= MAX_NODES_PER_SEGMENT
            if current and (
                too_many or current_len + len(t) + 8 > self.config.chunk_size
            ):
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
            translated = self._translate_chunk(joined, system_prompt)
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
                    slots[i][0].text = self._translate_chunk(slots[i][0].text or "", system_prompt)
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

        # Build system prompt once for all chunks
        system_prompt = self._build_system_prompt(skill_text)

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
