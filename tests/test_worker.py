"""Testy modułu worker.py — background workers dla tłumaczenia i serwera.

Moduł worker.py nie miał wcześniej bezpośrednich testów. Te testy weryfikują:
- Strukturę klas TranslateWorker, TranslationThread
- Sygnały Qt i sloty
- Logikę cancel (structure, nie pełny proces)
- Klasy ServerWorker (Start/Stop/Restart)
"""

import pytest
import multiprocessing as mp
from unittest.mock import MagicMock, patch


@pytest.fixture
def qapp():
    """QApplication fixture for Qt tests."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestTranslateWorker:
    """Testy klasy TranslateWorker."""

    def test_translate_worker_init(self, qapp):
        """TranslateWorker powinien się tworzyć bez błędów."""
        from tlumacz.qt_gui.worker import TranslateWorker
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        worker = TranslateWorker(
            config=config,
            input_path="/tmp/test.md",
            output_path="/tmp/test_pl.md",
        )
        
        assert worker is not None
        assert worker._config == config
        assert worker._input_path == "/tmp/test.md"
        assert worker._output_path == "/tmp/test_pl.md"

    def test_translate_worker_has_signals(self, qapp):
        """TranslateWorker powinien mieć sygnały Qt."""
        from tlumacz.qt_gui.worker import TranslateWorker
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        worker = TranslateWorker(config=config, input_path="/tmp/test.md", output_path="/tmp/test_pl.md")
        
        # Sprawdź że sygnały istnieją (rzeczywiste nazwy)
        assert hasattr(worker, 'finished')
        assert hasattr(worker, 'failed')
        assert hasattr(worker, 'progress')
        assert hasattr(worker, 'log')  # nie log_message

    def test_translate_worker_cancel_event(self, qapp):
        """TranslateWorker powinien mieć _cancel_event (inicjalizowane jako None)."""
        from tlumacz.qt_gui.worker import TranslateWorker
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        worker = TranslateWorker(config=config, input_path="/tmp/test.md", output_path="/tmp/test_pl.md")
        
        # _cancel_event jest inicjalizowane jako None, tworzone w run()
        assert hasattr(worker, '_cancel_event')
        assert worker._cancel_event is None  # przed run()

    def test_translate_worker_cancel_method(self, qapp):
        """TranslateWorker.cancel() powinien ustawiać _cancelled flag."""
        from tlumacz.qt_gui.worker import TranslateWorker
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        worker = TranslateWorker(config=config, input_path="/tmp/test.md", output_path="/tmp/test_pl.md")
        
        # Przed cancel
        assert not worker._cancelled
        
        # Cancel
        worker.cancel()
        
        # Po cancel
        assert worker._cancelled


class TestTranslationThread:
    """Testy klasy TranslationThread."""

    def test_translation_thread_init(self, qapp):
        """TranslationThread powinien się tworzyć bez błędów."""
        from tlumacz.qt_gui.worker import TranslationThread
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        thread = TranslationThread(
            config=config,
            input_path="/tmp/test.md",
            output_path="/tmp/test_pl.md",
        )
        
        assert thread is not None
        assert hasattr(thread, 'worker')
        assert hasattr(thread, 'thread')

    def test_translation_thread_has_signals(self, qapp):
        """TranslationThread powinien mieć sygnały jako properties."""
        from tlumacz.qt_gui.worker import TranslationThread
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        thread = TranslationThread(config=config, input_path="/tmp/test.md", output_path="/tmp/test_pl.md")
        
        # Sygnały są jako properties delegujące do worker
        assert hasattr(thread, 'finished')
        assert hasattr(thread, 'failed')
        assert hasattr(thread, 'progress')
        assert hasattr(thread, 'log')

    def test_translation_thread_cancel(self, qapp):
        """TranslationThread.cancel() powinien delegować do worker.cancel()."""
        from tlumacz.qt_gui.worker import TranslationThread
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        thread = TranslationThread(config=config, input_path="/tmp/test.md", output_path="/tmp/test_pl.md")
        
        # Przed cancel
        assert not thread.worker._cancelled
        
        # Cancel deleguje do worker
        thread.cancel()
        
        # Po cancel
        assert thread.worker._cancelled

    def test_translation_thread_has_stop(self, qapp):
        """TranslationThread powinien mieć metodę stop()."""
        from tlumacz.qt_gui.worker import TranslationThread
        from tlumacz.core import TranslatorConfig
        
        config = TranslatorConfig(
            base_url="http://test",
            api_key="test",
            model="test-model",
        )
        
        thread = TranslationThread(config=config, input_path="/tmp/test.md", output_path="/tmp/test_pl.md")
        
        assert hasattr(thread, 'stop')
        assert callable(thread.stop)


class TestServerWorkers:
    """Testy klas ServerWorker (Start/Stop/Restart)."""

    def test_start_worker_init(self, qapp):
        """StartWorker powinien się tworzyć bez błędów."""
        from tlumacz.qt_gui.worker import StartWorker
        from tlumacz.server import LlamaServer, ServerConfig
        
        server_config = ServerConfig()
        server = LlamaServer(server_config)
        
        worker = StartWorker(server)
        assert worker is not None
        assert worker._server == server

    def test_stop_worker_init(self, qapp):
        """StopWorker powinien się tworzyć bez błędów."""
        from tlumacz.qt_gui.worker import StopWorker
        from tlumacz.server import LlamaServer, ServerConfig
        
        server_config = ServerConfig()
        server = LlamaServer(server_config)
        
        worker = StopWorker(server)
        assert worker is not None

    def test_restart_worker_init(self, qapp):
        """RestartWorker powinien się tworzyć bez błędów."""
        from tlumacz.qt_gui.worker import RestartWorker
        from tlumacz.server import LlamaServer, ServerConfig
        
        server_config = ServerConfig()
        server = LlamaServer(server_config)
        
        # RestartWorker wymaga config_updates
        worker = RestartWorker(server, config_updates={})
        assert worker is not None

    def test_server_worker_has_signals(self, qapp):
        """ServerWorker powinien mieć sygnały."""
        from tlumacz.qt_gui.worker import StartWorker
        from tlumacz.server import LlamaServer, ServerConfig
        
        server_config = ServerConfig()
        server = LlamaServer(server_config)
        
        worker = StartWorker(server)
        
        # Sprawdź podstawowe sygnały
        assert hasattr(worker, 'finished')


class TestWorkerConstants:
    """Testy stałych i konfiguracji worker."""

    def test_cancel_timeouts_defined(self):
        """Stałe cancel timeout powinny być zdefiniowane."""
        from tlumacz.qt_gui import worker
        
        assert hasattr(worker, '_CANCEL_TERMINATE_AFTER_S')
        assert hasattr(worker, '_CANCEL_KILL_AFTER_S')
        
        # Wartości powinny być pozytywne
        assert worker._CANCEL_TERMINATE_AFTER_S > 0
        assert worker._CANCEL_KILL_AFTER_S > 0
        
        # Kill powinien być po terminate
        assert worker._CANCEL_KILL_AFTER_S > worker._CANCEL_TERMINATE_AFTER_S
