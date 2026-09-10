"""Testy modułu fastapi_manager.py — manager serwera FastAPI.

Te testy weryfikują:
- Inicjalizację managera i konfigurację
- Przejścia stanów (IDLE → STARTING → RUNNING → STOPPING)
- Właściwości (state, is_running, base_url)
- Metody start/stop/restart z mockowanym serwerem
- Health check
- Zarządzanie błędami
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import time


# ============================================================================
# Testy konfiguracji
# ============================================================================

class TestFastAPIServerManagerConfig:
    """Testy klasy FastAPIServerManagerConfig."""

    def test_default_config(self):
        """Domyślna konfiguracja powinna mieć rozsądne wartości."""
        from tlumacz.fastapi_manager import FastAPIServerManagerConfig

        config = FastAPIServerManagerConfig()
        assert config.model_path == "google/translategemma-4b-it"
        assert config.host == "127.0.0.1"
        assert config.port == 8001
        assert config.device == "auto"
        assert config.dtype == "float16"
        assert config.auto_start is False

    def test_custom_config(self):
        """Można utworzyć konfigurację z niestandardowymi wartościami."""
        from tlumacz.fastapi_manager import FastAPIServerManagerConfig

        config = FastAPIServerManagerConfig(
            model_path="/custom/model",
            host="0.0.0.0",
            port=9000,
            device="cpu",
            dtype="float32",
            auto_start=True,
        )
        assert config.model_path == "/custom/model"
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.device == "cpu"
        assert config.dtype == "float32"
        assert config.auto_start is True


# ============================================================================
# Testy FastAPIServerManager
# ============================================================================

class TestFastAPIServerManager:
    """Testy klasy FastAPIServerManager."""

    def test_manager_init_default(self):
        """Manager powinien się tworzyć z domyślną konfiguracją."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        assert manager.state == FastAPIServerManager.IDLE
        assert not manager.is_running
        assert manager._server is None
        assert manager._last_error == ""

    def test_manager_init_custom_config(self):
        """Manager powinien się tworzyć z niestandardową konfiguracją."""
        from tlumacz.fastapi_manager import FastAPIServerManager, FastAPIServerManagerConfig

        config = FastAPIServerManagerConfig(
            model_path="/custom/model",
            port=9999,
        )
        manager = FastAPIServerManager(config)
        assert manager._config.model_path == "/custom/model"
        assert manager._config.port == 9999

    def test_manager_states_defined(self):
        """Stany managera powinny być zdefiniowane."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        assert FastAPIServerManager.IDLE == "idle"
        assert FastAPIServerManager.STARTING == "starting"
        assert FastAPIServerManager.RUNNING == "running"
        assert FastAPIServerManager.STOPPING == "stopping"

    def test_manager_initial_state_is_idle(self):
        """Początkowy stan managera powinien być IDLE."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        assert manager.state == FastAPIServerManager.IDLE

    def test_base_url(self):
        """base_url powinien zwracać poprawny URL."""
        from tlumacz.fastapi_manager import FastAPIServerManager, FastAPIServerManagerConfig

        config = FastAPIServerManagerConfig(host="127.0.0.1", port=8001)
        manager = FastAPIServerManager(config)

        assert manager.base_url == "http://127.0.0.1:8001/v1"

    def test_base_url_custom(self):
        """base_url powinien używać niestandardowych wartości host/port."""
        from tlumacz.fastapi_manager import FastAPIServerManager, FastAPIServerManagerConfig

        config = FastAPIServerManagerConfig(host="0.0.0.0", port=9999)
        manager = FastAPIServerManager(config)

        assert manager.base_url == "http://0.0.0.0:9999/v1"

    def test_is_running_false_initially(self):
        """is_running powinno zwracać False na początku."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        assert not manager.is_running

    def test_is_running_true_when_running(self):
        """is_running powinno zwracać True gdy serwer działa."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager._state = FastAPIServerManager.RUNNING
        manager._server = MagicMock()
        manager._server.is_running.return_value = True

        assert manager.is_running

    def test_is_running_false_when_server_not_running(self):
        """is_running powinno zwracać False gdy serwer nie działa."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager._state = FastAPIServerManager.RUNNING
        manager._server = MagicMock()
        manager._server.is_running.return_value = False

        assert not manager.is_running

    def test_get_last_error_empty_initially(self):
        """get_last_error powinno zwracać pusty string na początku."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        assert manager.get_last_error() == ""

    def test_get_last_error_after_failure(self):
        """get_last_error powinno zwracać błąd po nieudanej operacji."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager._last_error = "Test error"
        assert manager.get_last_error() == "Test error"


# ============================================================================
# Testy start/stop/restart z mockowanym serwerem
# ============================================================================

class TestManagerStartStop:
    """Testy metod start/stop/restart z mockowanym serwerem."""

    def test_stop_when_not_running(self):
        """stop() powinno być bezpieczne gdy serwer nie działa."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager.stop()  # nie powinno rzucić wyjątku
        assert manager.state == FastAPIServerManager.IDLE

    def test_stop_sets_state_to_idle(self):
        """stop() powinno ustawić stan na IDLE."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager._state = FastAPIServerManager.RUNNING
        manager._server = MagicMock()

        manager.stop()
        assert manager.state == FastAPIServerManager.IDLE
        assert manager._server is None

    def test_start_already_running(self):
        """start() powinno zwrócić True gdy serwer już działa."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager._state = FastAPIServerManager.RUNNING

        result = manager.start()
        assert result is True

    def test_start_already_starting(self):
        """start() powinno zwrócić False gdy serwer już się uruchamia."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()
        manager._state = FastAPIServerManager.STARTING

        result = manager.start()
        assert result is False

    @patch("tlumacz.fastapi_manager.TranslateGemmaServer")
    def test_start_creates_server(self, MockServer):
        """start() powinno utworzyć instancję TranslateGemmaServer."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        mock_server_instance = MagicMock()
        mock_server_instance.is_running.return_value = True
        MockServer.return_value = mock_server_instance

        manager = FastAPIServerManager()

        # Mock _wait_ready i _health_check
        manager._wait_ready = MagicMock(return_value=True)

        result = manager.start()
        assert result is True
        assert manager._server is not None
        assert manager.state == FastAPIServerManager.RUNNING

    @patch("tlumacz.fastapi_manager.TranslateGemmaServer")
    def test_start_failure_sets_idle(self, MockServer):
        """start() powinno ustawić stan na IDLE przy błędzie."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        mock_server_instance = MagicMock()
        mock_server_instance.start.side_effect = Exception("Start failed")
        MockServer.return_value = mock_server_instance

        manager = FastAPIServerManager()
        result = manager.start()

        assert result is False
        assert manager.state == FastAPIServerManager.IDLE
        assert manager.get_last_error() != ""

    @patch("tlumacz.fastapi_manager.TranslateGemmaServer")
    def test_restart_calls_stop_and_start(self, MockServer):
        """restart() powinno wywołać stop() i start()."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        mock_server_instance = MagicMock()
        mock_server_instance.is_running.return_value = True
        MockServer.return_value = mock_server_instance

        manager = FastAPIServerManager()
        manager._wait_ready = MagicMock(return_value=True)

        # Najpierw uruchom
        manager.start()
        assert manager.state == FastAPIServerManager.RUNNING

        # Potem restart
        result = manager.restart()
        assert result is True


# ============================================================================
# Testy health check
# ============================================================================

class TestHealthCheck:
    """Testy metody _health_check()."""

    def test_health_check_success(self):
        """_health_check() powinno zwrócić True gdy serwer odpowiada."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()

        # Mock urllib.request.urlopen
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = manager._health_check()
            assert result is True

    def test_health_check_failure(self):
        """_health_check() powinno zwrócić False gdy serwer nie odpowiada."""
        from tlumacz.fastapi_manager import FastAPIServerManager

        manager = FastAPIServerManager()

        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            result = manager._health_check()
            assert result is False


# ============================================================================
# Testy update_config
# ============================================================================

class TestUpdateConfig:
    """Testy metody update_config()."""

    def test_update_config_changes_values(self):
        """update_config() powinno zmienić wartości konfiguracji."""
        from tlumacz.fastapi_manager import FastAPIServerManager, FastAPIServerManagerConfig

        manager = FastAPIServerManager()
        new_config = FastAPIServerManagerConfig(
            model_path="/new/model",
            port=9999,
        )

        manager.update_config(new_config)
        assert manager._config.model_path == "/new/model"
        assert manager._config.port == 9999

    def test_update_config_stops_running_server(self):
        """update_config() powinno zatrzymać działający serwer."""
        from tlumacz.fastapi_manager import FastAPIServerManager, FastAPIServerManagerConfig

        manager = FastAPIServerManager()
        manager._state = FastAPIServerManager.RUNNING
        mock_server = MagicMock()
        manager._server = mock_server

        new_config = FastAPIServerManagerConfig()

        # Mock start() żeby nie próbował naprawdę uruchamiać serwera
        with patch.object(manager, 'start', return_value=True):
            manager.update_config(new_config)

        # Serwer powinien zostać zatrzymany (stop() wywołane)
        mock_server.stop.assert_called_once()
