"""Testy jednostkowe dla BackendManager.

Testy weryfikują:
- Przełączanie backendów (llama/cloud/fastapi)
- Cykl życia (start/stop/restart)
- Sygnały Qt
- Walidacja konfiguracji
- Kompatybilność z ServerManager i FastAPIServerManager
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from tlumacz.qt_gui.backend_manager import BackendManager, BackendConfig


# ---------------------------------------------------------------------------
# Fixture'y
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    """Jedna instancja QApplication dla wszystkich testów."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def backend_manager(qapp):
    """BackendManager z domyślną konfiguracją."""
    return BackendManager(BackendConfig())


@pytest.fixture
def mock_server_manager():
    """Mock ServerManager z podstawowymi metodami i sygnałami."""
    from PySide6.QtCore import Signal, QObject

    class MockServerManager(QObject):
        server_started = Signal(str)
        server_stopped = Signal()
        server_error = Signal(str)
        operation_finished = Signal()

        def __init__(self):
            super().__init__()
            self._is_running = False
            self._last_error = ""
            self._base_url = "http://127.0.0.1:18080/v1"
            self._config = MagicMock()
            self._config.base_url = self._base_url
            self.server = MagicMock()
            self.server.config.base_url = self._base_url

        @property
        def is_running(self):
            return self._is_running

        def start(self):
            self._is_running = True

        def stop(self):
            self._is_running = False

        def restart(self, config_updates=None):
            self._is_running = True

        def get_last_error(self):
            return self._last_error

    return MockServerManager()


# ---------------------------------------------------------------------------
# Testy BackendConfig
# ---------------------------------------------------------------------------

class TestBackendConfig:
    """Testy konfiguracji backendu."""

    def test_default_backend_is_llama(self):
        """Domyślny backend to llama."""
        config = BackendConfig()
        assert config.backend_type == "llama"

    def test_validate_valid_backends(self):
        """Walidacja przechodzi dla znanych backendów."""
        for backend in ("llama", "cloud", "fastapi"):
            config = BackendConfig(backend_type=backend)
            config.validate()  # Nie powinno rzucić wyjątku

    def test_validate_invalid_backend(self):
        """Walidacja rzuca ValueError dla nieznanego backendu."""
        config = BackendConfig(backend_type="invalid")
        with pytest.raises(ValueError, match="Nieznany backend"):
            config.validate()

    def test_fastapi_defaults(self):
        """Domyślne wartości FastAPI są poprawne."""
        config = BackendConfig()
        assert config.fastapi_model_path == "google/translategemma-4b-it"
        assert config.fastapi_host == "127.0.0.1"
        assert config.fastapi_port == 8001
        assert config.fastapi_device == "auto"
        assert config.fastapi_dtype == "float16"


# ---------------------------------------------------------------------------
# Testy BackendManager — podstawowe
# ---------------------------------------------------------------------------

class TestBackendManagerBasic:
    """Podstawowe testy BackendManager."""

    def test_default_backend(self, backend_manager):
        """Domyślny backend to llama."""
        assert backend_manager.get_active_backend() == "llama"

    def test_switch_to_fastapi(self, backend_manager):
        """Zmiana backendu na fastapi."""
        backend_manager.set_active_backend("fastapi")
        assert backend_manager.get_active_backend() == "fastapi"

    def test_switch_to_cloud(self, backend_manager):
        """Zmiana backendu na cloud."""
        backend_manager.set_active_backend("cloud")
        assert backend_manager.get_active_backend() == "cloud"

    def test_switch_back_to_llama(self, backend_manager):
        """Zmiana backendu z powrotem na llama."""
        backend_manager.set_active_backend("fastapi")
        backend_manager.set_active_backend("llama")
        assert backend_manager.get_active_backend() == "llama"

    def test_invalid_backend_raises(self, backend_manager):
        """Nieznany backend rzuca ValueError."""
        with pytest.raises(ValueError, match="Nieznany backend"):
            backend_manager.set_active_backend("invalid")


# ---------------------------------------------------------------------------
# Testy BackendManager — cykl życia
# ---------------------------------------------------------------------------

class TestBackendManagerLifecycle:
    """Testy cyklu życia backendu."""

    def test_cloud_always_running(self, qapp):
        """Cloud zawsze 'działa'."""
        manager = BackendManager(BackendConfig(
            backend_type="cloud",
            cloud_base_url="https://api.example.com"
        ))
        assert manager.is_running() is True

    def test_cloud_start_emits_signal(self, qapp):
        """Start cloud emituje backend_started."""
        manager = BackendManager(BackendConfig(
            backend_type="cloud",
            cloud_base_url="https://api.example.com"
        ))
        emitted = []
        manager.backend_started.connect(lambda url: emitted.append(url))
        manager.start()
        assert emitted == ["https://api.example.com"]

    def test_cloud_no_base_url_emits_error(self, qapp):
        """Brak cloud_base_url emituje backend_error."""
        manager = BackendManager(BackendConfig(backend_type="cloud"))
        errors = []
        manager.backend_error.connect(lambda msg: errors.append(msg))
        manager.start()
        assert len(errors) == 1
        assert "cloud_base_url" in errors[0]

    def test_llama_not_running_without_server_manager(self, backend_manager):
        """llama nie działa bez ServerManager."""
        assert backend_manager.is_running() is False

    def test_llama_start_without_server_manager_emits_error(self, backend_manager):
        """Start llama bez ServerManager emituje błąd."""
        errors = []
        backend_manager.backend_error.connect(lambda msg: errors.append(msg))
        backend_manager.start()
        assert len(errors) == 1
        assert "ServerManager" in errors[0]


# ---------------------------------------------------------------------------
# Testy BackendManager — integracja z ServerManager
# ---------------------------------------------------------------------------

class TestBackendManagerWithServerManager:
    """Testy integracji z ServerManager."""

    def test_set_server_manager(self, backend_manager, mock_server_manager):
        """Wstrzyknięcie ServerManager działa."""
        backend_manager.set_server_manager(mock_server_manager)
        assert backend_manager._server_manager is mock_server_manager

    def test_llama_is_running_delegates(self, backend_manager, mock_server_manager):
        """is_running dla llama deleguje do ServerManager."""
        backend_manager.set_server_manager(mock_server_manager)
        mock_server_manager._is_running = True
        assert backend_manager.is_running() is True
        mock_server_manager._is_running = False
        assert backend_manager.is_running() is False

    def test_llama_start_delegates(self, backend_manager, mock_server_manager):
        """start() dla llama deleguje do ServerManager."""
        backend_manager.set_server_manager(mock_server_manager)
        backend_manager.start()
        assert mock_server_manager._is_running is True

    def test_llama_stop_delegates(self, backend_manager, mock_server_manager):
        """stop() dla llama deleguje do ServerManager."""
        backend_manager.set_server_manager(mock_server_manager)
        mock_server_manager._is_running = True
        backend_manager.stop()
        assert mock_server_manager._is_running is False

    def test_llama_get_base_url(self, backend_manager, mock_server_manager):
        """get_base_url() dla llama odczytuje z ServerManager."""
        backend_manager.set_server_manager(mock_server_manager)
        url = backend_manager.get_base_url()
        assert url == "http://127.0.0.1:18080/v1"

    def test_server_error_propagated(self, backend_manager, mock_server_manager):
        """Błąd z ServerManager jest propagowany przez BackendManager."""
        backend_manager.set_server_manager(mock_server_manager)
        errors = []
        backend_manager.backend_error.connect(lambda msg: errors.append(msg))
        mock_server_manager.server_error.emit("Test error")
        assert errors == ["Test error"]
        assert backend_manager.get_last_error() == "Test error"


# ---------------------------------------------------------------------------
# Testy BackendManager — get_base_url
# ---------------------------------------------------------------------------

class TestBackendManagerBaseUrl:
    """Testy get_base_url dla różnych backendów."""

    def test_cloud_base_url(self, qapp):
        """Cloud zwraca cloud_base_url z konfiguracji."""
        manager = BackendManager(BackendConfig(
            backend_type="cloud",
            cloud_base_url="https://gemini.example.com/v1"
        ))
        assert manager.get_base_url() == "https://gemini.example.com/v1"

    def test_fastapi_base_url(self, qapp):
        """FastAPI zwraca base_url z FastAPIServerManager."""
        manager = BackendManager(BackendConfig(backend_type="fastapi"))
        url = manager.get_base_url()
        assert "8001" in url

    def test_llama_empty_without_server(self, backend_manager):
        """llama bez ServerManager zwraca pusty string."""
        assert backend_manager.get_base_url() == ""


# ---------------------------------------------------------------------------
# Testy BackendManager — restart
# ---------------------------------------------------------------------------

class TestBackendManagerRestart:
    """Testy restartu backendu."""

    def test_cloud_restart_is_noop(self, qapp):
        """Restart cloud nic nie robi."""
        manager = BackendManager(BackendConfig(
            backend_type="cloud",
            cloud_base_url="https://api.example.com"
        ))
        manager.restart()  # Nie powinno rzucić wyjątku

    def test_llama_restart_delegates(self, backend_manager, mock_server_manager):
        """Restart llama deleguje do ServerManager."""
        backend_manager.set_server_manager(mock_server_manager)
        mock_server_manager._is_running = True
        backend_manager.restart()
        # restart wywołuje stop() i start()
        # ServerManager.start() ustawia _is_running = True
        assert mock_server_manager._is_running is True
