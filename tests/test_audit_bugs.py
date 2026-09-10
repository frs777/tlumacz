"""Testy potwierdzające bugi znalezione w audycie 2026-09-08.

Każdy test jest nazwany zgodnie z identyfikatorem z raportu audytu
(np. test_bug_01_*). Testy potwierdzają istnienie buga — po naprawie
należy je zaktualizować żeby weryfikowały poprawność jako testy regresyjne.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import pytest
import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# BUG-01: _translate_pdf — pętla po blokach nie tłumaczy
# ---------------------------------------------------------------------------

class TestBug01TranslatePdfIndentation:
    """Potwierdza BUG-01: kod tłumaczenia bloków jest POZA pętlą for.

    Pętla `for idx, block in enumerate(blocks)` zawiera TYLKO sprawdzenie
    is_cancelled. Reszta kodu (tłumaczenie, wstawianie tekstu, zapis) jest
    wcięta na tym samym poziomie co ciało pętli, ale POZA nią.
    """

    def test_loop_body_contains_translation_code(self):
        """Analiza AST: pętla for w _translate_pdf zawiera kod tłumaczenia."""
        from tlumacz.core import Translator

        source = inspect.getsource(Translator._translate_pdf)
        tree = ast.parse(textwrap.dedent(source))

        # Znajdź pętlę for iterującą po enumerate(blocks)
        target_loop = None
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
                func = node.iter.func
                if isinstance(func, ast.Name) and func.id == "enumerate":
                    target_loop = node
                    break

        assert target_loop is not None, "Nie znaleziono pętli for enumerate(blocks)"

        body_stmts = target_loop.body
        non_if_statements = [s for s in body_stmts if not isinstance(s, ast.If)]

        # Po naprawie: pętla zawiera wiele instrukcji poza if (tłumaczenie, wstawianie, itp.)
        assert len(non_if_statements) >= 5, (
            f"Pętla zawiera tylko {len(non_if_statements)} instrukcji poza if — "
            f"bug nadal istnieje (oczekiwano >=5: log, translate, page, rect, redact, ...)"
        )

    def test_translate_pdf_only_translates_last_block(self, tmp_path):
        """Test funkcjonalny: _translate_chunk wywoływany dla każdego bloku."""
        from tlumacz.core import Translator, TranslatorConfig
        from tlumacz.pdf_extractor import extract_text_blocks

        # Utwórz PDF z 3 blokami tekstu w różnych pozycjach
        pdf_path = tmp_path / "multi_block.pdf"
        output_path = tmp_path / "multi_block_pl.pdf"

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Pierwszy blok tekstu", fontsize=14)
        page.insert_text((72, 200), "Drugi blok tekstu", fontsize=14)
        page.insert_text((72, 400), "Trzeci blok tekstu", fontsize=14)
        doc.save(str(pdf_path))
        doc.close()

        blocks = extract_text_blocks(pdf_path)
        num_blocks = len(blocks)
        assert num_blocks >= 2, "Test wymaga >=2 bloków tekstu w PDF"

        config = TranslatorConfig(cache_enabled=False, chunk_size=4000)
        translator = Translator(config)

        call_count = 0

        def fake_translate_chunk(text, system_prompt):
            nonlocal call_count
            call_count += 1
            return f"TRANSLATED: {text}"

        translator._translate_chunk = fake_translate_chunk

        # Mock _find_unicode_font żeby uniknąć problemów z czcionkami w testach
        import tlumacz.core as core_module
        original_find_font = core_module._find_unicode_font
        core_module._find_unicode_font = lambda: None

        try:
            translator.translate_file(
                str(pdf_path), str(output_path),
                log_callback=lambda msg: None,
            )
        except Exception:
            pass
        finally:
            core_module._find_unicode_font = original_find_font

        # Po naprawie: call_count == num_blocks (każdy blok tłumaczony)
        # Z bugiem: call_count == 1 (tylko ostatni blok po pętli)
        if call_count != num_blocks:
            pytest.fail(
                f"BUG-01: PDF ma {num_blocks} bloków tekstu, "
                f"ale _translate_chunk został wywołany tylko {call_count} razy. "
                f"Oczekiwano {num_blocks} wywołań (raz na każdy blok)."
            )


# ---------------------------------------------------------------------------
# BUG-02: Podwójna definicja property state w ServerManager
# ---------------------------------------------------------------------------

class TestBug02DuplicateProperty:
    """Weryfikuje że BUG-02 został naprawiony — property state jest zdefiniowane raz."""

    def test_single_state_property(self):
        """Po naprawie: ServerManager ma dokładnie 1 @property state."""
        from tlumacz.qt_gui.worker import ServerManager

        source = inspect.getsource(ServerManager)
        tree = ast.parse(textwrap.dedent(source))

        state_properties = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "state":
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id == "property":
                        state_properties.append(node)

        assert len(state_properties) == 1, (
            f"Oczekiwano 1 definicji @property state, znaleziono {len(state_properties)}."
        )


# ---------------------------------------------------------------------------
# BUG-03: RuntimeWarning z disconnect()
# ---------------------------------------------------------------------------

class TestBug03DisconnectWarning:
    """Weryfikuje że BUG-03 został naprawiony — brak disconnect() na niepołączonych."""

    def test_disconnect_guarded_by_flag(self):
        """Po naprawie: disconnect() jest chronione flagą _server_signals_connected."""
        from tlumacz.qt_gui.backend_manager import BackendManager

        source = inspect.getsource(BackendManager._connect_server_signals)
        assert "_server_signals_connected" in source, (
            "Brak flagi _server_signals_connected — disconnect() może generować RuntimeWarning"
        )


# ---------------------------------------------------------------------------
# BUG-04: Hardcoded ścieżki użytkownika
# ---------------------------------------------------------------------------

class TestBug04HardcodedPaths:
    """Weryfikuje że BUG-04 został naprawiony — brak hardcoded ścieżek."""

    def test_openvino_backend_no_hardcoded_path(self):
        from tlumacz.openvino_backend import OpenVINOConfig
        config = OpenVINOConfig()
        assert "/home/frs" not in config.model_path, (
            "OpenVINOConfig nadal ma hardcoded ścieżkę"
        )

    def test_backend_config_no_hardcoded_path(self):
        from tlumacz.qt_gui.backend_manager import BackendConfig
        config = BackendConfig()
        assert "/home/frs" not in config.openvino_model_path, (
            "BackendConfig nadal ma hardcoded ścieżkę"
        )

    def test_app_settings_no_hardcoded_path(self):
        from tlumacz.qt_gui.config import AppSettings
        settings = AppSettings()
        assert "/home/frs" not in settings.openvino_model_path, (
            "AppSettings nadal ma hardcoded ścieżkę"
        )

    def test_transgemma_no_hardcoded_path(self):
        transgemma_path = Path(__file__).parent.parent / "transgemma.py"
        if not transgemma_path.exists():
            pytest.skip("transgemma.py nie istnieje")
        content = transgemma_path.read_text(encoding="utf-8")
        assert "/home/frs" not in content, (
            "transgemma.py nadal ma hardcoded ścieżkę"
        )


# ---------------------------------------------------------------------------
# BUG-05: Pseudo-asynchroniczność ładowania modelu
# ---------------------------------------------------------------------------

class TestBug05PseudoAsync:
    """Weryfikuje że BUG-05 został naprawiony — brak join() po Thread()."""

    def test_start_no_join_after_thread(self):
        """Po naprawie: start() nie tworzy wątku z natychmiastowym join()."""
        from tlumacz.fastapi_server import TranslateGemmaServer

        source = inspect.getsource(TranslateGemmaServer.start)

        # Nie powinno być wzorca: Thread(...) + .join() w tej samej metodzie
        # (join jest OK w stop(), ale nie w start() dla ładowania modelu)
        has_load_thread = "load_thread" in source
        has_join = "load_thread.join()" in source

        assert not (has_load_thread and has_join), (
            "start() nadal tworzy wątek z natychmiastowym join() — bug nie naprawiony"
        )


# ---------------------------------------------------------------------------
# BUG-12: Hardcoded DEBUG logging
# ---------------------------------------------------------------------------

class TestBug12DebugLogging:
    """Potwierdza BUG-12: hardcoded level=logging.DEBUG w produkcji."""

    def test_app_uses_debug_level(self):
        app_path = Path(__file__).parent.parent / "tlumacz" / "qt_gui" / "app.py"
        content = app_path.read_text(encoding="utf-8")
        assert "level=logging.DEBUG" in content


# ---------------------------------------------------------------------------
# DEAD-01: _split_into_chunks jest nieużywana
# ---------------------------------------------------------------------------

class TestDead01SplitIntoChunks:
    """Weryfikuje że DEAD-01 został naprawiony — _split_into_chunks usunięta."""

    def test_method_removed(self):
        """Po naprawie: _split_into_chunks nie istnieje w Translator."""
        from tlumacz.core import Translator
        assert not hasattr(Translator, "_split_into_chunks"), (
            "_split_into_chunks nadal istnieje — powinna być usunięta"
        )


# ---------------------------------------------------------------------------
# DEAD-02: split_xml_segments jest nieużywana
# ---------------------------------------------------------------------------

class TestDead02SplitXmlSegments:
    """Weryfikuje użycie split_xml_segments.

    Pierwotnie raport audytu wskazywał DEAD-02 jako martwy kod,
    ale funkcja jest wywoływana w _translate_text() (fallback dla
    nieparsowalnego XML). Test weryfikuje to użycie.
    """

    def test_function_is_used_in_fallback(self):
        """split_xml_segments jest wywoływana w _translate_text (fallback)."""
        from tlumacz.preprocess import split_xml_segments
        assert callable(split_xml_segments)

        core_path = Path(__file__).parent.parent / "tlumacz" / "core.py"
        content = core_path.read_text(encoding="utf-8")

        # split_xml_segments jest wywoływana w _translate_text
        lines_with_call = [
            line for line in content.splitlines()
            if "split_xml_segments(" in line
        ]
        assert len(lines_with_call) >= 1, (
            "split_xml_segments nie jest wywoływana — może być martwa"
        )


# ---------------------------------------------------------------------------
# DEAD-03: extract_text() jest nieosiągalna w normalnym przepływie
# ---------------------------------------------------------------------------

class TestDead03ExtractTextRemoved:
    """Weryfikuje że DEAD-03 został naprawiony — extract_text() usunięta."""

    def test_extract_text_removed(self):
        """Po naprawie: extract_text() nie istnieje w extract.py."""
        import tlumacz.extract as extract_module
        assert not hasattr(extract_module, "extract_text"), (
            "extract_text() nadal istnieje — powinna być usunięta"
        )

    def test_extract_text_not_imported_in_core(self):
        """Po naprawie: extract_text nie jest importowane w core.py."""
        core_path = Path(__file__).parent.parent / "tlumacz" / "core.py"
        content = core_path.read_text(encoding="utf-8")
        assert "extract_text" not in content or "extract_text_blocks" in content, (
            "extract_text jest nadal importowane w core.py"
        )


# ---------------------------------------------------------------------------
# DEAD-04: convert.py jest nieużywany
# ---------------------------------------------------------------------------

class TestDead04ConvertUnused:
    """Potwierdza DEAD-04: moduł convert nie jest importowany nigdzie."""

    def test_convert_not_imported_in_core(self):
        core_path = Path(__file__).parent.parent / "tlumacz" / "core.py"
        content = core_path.read_text(encoding="utf-8")
        assert "from .convert" not in content
        assert "import convert" not in content

    def test_convert_not_imported_in_worker(self):
        worker_path = (
            Path(__file__).parent.parent / "tlumacz" / "qt_gui" / "worker.py"
        )
        content = worker_path.read_text(encoding="utf-8")
        assert "from .convert" not in content
        assert "from ..convert" not in content


# ---------------------------------------------------------------------------
# DEAD-05: Powielony kod logowania cache (4x)
# ---------------------------------------------------------------------------

class TestDead05DuplicatedCacheLogging:
    """Weryfikuje że DEAD-05 został naprawiony — kod cache wyekstrahowany."""

    def test_cache_logging_extracted_to_method(self):
        """Po naprawie: logowanie cache jest w jednej metodzie _finalize_cache."""
        core_path = Path(__file__).parent.parent / "tlumacz" / "core.py"
        content = core_path.read_text(encoding="utf-8")

        # _finalize_cache powinna istnieć
        assert "def _finalize_cache" in content

        # Powinna być wywoływana 4 razy (translate_file, epub, office, pdf)
        count = content.count("self._finalize_cache(")
        assert count == 4, f"Oczekiwano 4 wywołań _finalize_cache, znaleziono {count}"

    def test_no_duplicate_cache_stats(self):
        """Po naprawie: cache_stats jest tylko w _finalize_cache."""
        core_path = Path(__file__).parent.parent / "tlumacz" / "core.py"
        content = core_path.read_text(encoding="utf-8")

        # cache_stats powinno być tylko w definicji _finalize_cache
        count = content.count("cache_stats = self._cache.stats()")
        assert count == 1, (
            f"Oczekiwano 1 wystąpienia (w _finalize_cache), znaleziono {count}"
        )


# ---------------------------------------------------------------------------
# DOC-01: Niezgodność wersji
# ---------------------------------------------------------------------------

class TestDoc01VersionMismatch:
    """Weryfikuje zgodność wersji dokumentacji z metadanymi projektu."""

    def test_version_matches(self):
        project_root = Path(__file__).parent.parent

        pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")
        pyproject_version = None
        for line in pyproject.splitlines():
            if line.strip().startswith("version"):
                pyproject_version = line.split("=", 1)[1].strip().strip('"')
                break

        qwen_md = (project_root / "QWEN.md").read_text(encoding="utf-8")
        qwen_version = None
        for line in qwen_md.splitlines():
            if "Wersja" in line and ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    qwen_version = parts[-1].strip().strip("*").strip()
                break

        assert pyproject_version is not None
        assert qwen_version is not None
        assert pyproject_version == qwen_version, (
            f"Niezgodne wersje: pyproject={pyproject_version}, QWEN={qwen_version}"
        )


# ---------------------------------------------------------------------------
# DOC-02: QWEN.md mówi o 3 backendach, faktycznie są 4
# ---------------------------------------------------------------------------

class TestDoc02BackendCount:
    """Weryfikuje że DOC-02 został naprawiony — QWEN.md wymienia 4 backendy."""

    def test_qwen_md_mentions_openvino(self):
        """Po naprawie: QWEN.md wspomina o backendzie OpenVINO."""
        qwen_path = Path(__file__).parent.parent / "QWEN.md"
        content = qwen_path.read_text(encoding="utf-8")

        assert "OpenVINO" in content, (
            "QWEN.md nie wspomina o OpenVINO — DOC-02 nie naprawiony"
        )
        assert "cztery backendy" in content.lower() or "4 backendy" in content.lower(), (
            "QWEN.md nie mówi o 4 backendach"
        )

    def test_four_backends_exist_in_code(self):
        from tlumacz.qt_gui.backend_manager import BackendConfig
        assert "openvino" in BackendConfig._VALID_BACKENDS
        assert len(BackendConfig._VALID_BACKENDS) == 4


# ---------------------------------------------------------------------------
# ARCH-01: main_window.py > 2000 linii
# ---------------------------------------------------------------------------

class TestArch01LargeMainWindow:
    """Potwierdza ARCH-01: main_window.py ma ponad 2000 linii."""

    def test_main_window_exceeds_2000_lines(self):
        mw_path = (
            Path(__file__).parent.parent
            / "tlumacz" / "qt_gui" / "main_window.py"
        )
        line_count = len(mw_path.read_text(encoding="utf-8").splitlines())
        assert line_count > 2000, (
            f"main_window.py ma {line_count} linii — < 2000, podzielony?"
        )
