"""Backend Manager for Tłumacz GUI.

Zarządza wyborem backendu tłumaczenia (llama.cpp, Cloud, FastAPI, OpenVINO).
Deleguje żądania do odpowiedniego managera.
Dziedziczy po QObject dla komunikacji z GUI przez sygnały Qt.

Architektura:
    BackendManager (QObject)
    ├── ServerManager (QObject, llama.cpp) — wstrzykiwany z MainWindow
    ├── FastAPIServerManager (Transformers) — tworzony wewnętrznie
    ├── OpenVINOBackend — tworzony wewnętrznie (lazy)
    └── Cloud API — bezpośredni URL z konfiguracji
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QObject, Signal, QThread

from .worker import ServerManager

logger = logging.getLogger(__name__)

# Lazy import OpenVINOBackend — openvino-genai może nie być zainstalowane
_OpenVINOBackend = None
_OpenVINOConfig = None


def _get_openvino_classes():
    """Lazy import OpenVINOBackend i OpenVINOConfig."""
    global _OpenVINOBackend, _OpenVINOConfig
    if _OpenVINOBackend is None:
        try:
            from ..openvino_backend import OpenVINOBackend, OpenVINOConfig
            _OpenVINOBackend = OpenVINOBackend
            _OpenVINOConfig = OpenVINOConfig
        except ImportError:
            logger.warning(
                "OpenVINOBackend niedostępny — brak zależności (openvino-genai). "
                "Zainstaluj: pip install openvino openvino-genai"
            )
    return _OpenVINOBackend, _OpenVINOConfig


# ---------------------------------------------------------------------------
# Konfiguracja
# ---------------------------------------------------------------------------

@dataclass
class BackendConfig:
    """Konfiguracja backendu tłumaczenia.

    Atrybuty:
        backend_type: Typ backendu — 'llama', 'cloud' lub 'fastapi'.
        server_port: Port serwera llama.cpp.
        server_gguf_path: Ścieżka do modelu GGUF.
        server_chat_template: Szablon czatu — 'jinja' lub 'chatml'.
        server_compute_mode: Tryb obliczeń — 'cpu' lub 'gpu'.
        server_parallel: Liczba równoległych żądań.
        cloud_base_url: URL API cloud (np. Gemini, OpenAI).
        cloud_api_key: Klucz API dla cloud.
        cloud_model: Nazwa modelu cloud.
        fastapi_model_path: Ścieżka do modelu lub nazwa z HuggingFace.
        fastapi_host: Host serwera FastAPI.
        fastapi_port: Port serwera FastAPI.
        fastapi_device: Urządzenie — 'auto', 'cpu' lub 'cuda'.
        fastapi_dtype: Typ danych — 'float16', 'bfloat16' lub 'float32'.
    """

    backend_type: str = "llama"

    # llama.cpp
    server_port: int = 17580
    server_gguf_path: str = ""
    server_chat_template: str = "jinja"
    server_compute_mode: str = "gpu"
    server_parallel: int = 1

    # Cloud API
    cloud_base_url: str = ""
    cloud_api_key: str = ""
    cloud_model: str = ""

    # FastAPI (TranslateGemma)
    fastapi_model_path: str = "google/translategemma-4b-it"
    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 8001
    fastapi_device: str = "auto"
    fastapi_dtype: str = "float16"

    # OpenVINO (TranslateGemma INT8)
    openvino_model_path: str = ""
    openvino_device: str = "CPU"

    # Walidacja
    _VALID_BACKENDS = ("llama", "cloud", "fastapi", "openvino")

    def validate(self) -> None:
        """Sprawdź poprawność konfiguracji.

        Raises:
            ValueError: Jeśli backend_type jest nieznany.
        """
        if self.backend_type not in self._VALID_BACKENDS:
            raise ValueError(
                f"Nieznany backend: {self.backend_type!r}. "
                f"Dozwolone: {self._VALID_BACKENDS}"
            )


# ---------------------------------------------------------------------------
# Worker dla FastAPI start (QThread)
# ---------------------------------------------------------------------------

class FastAPIStartWorker(QObject):
    """Worker uruchamiający FastAPI w tle (nie blokuje GUI)."""

    finished = Signal(bool)  # success
    error = Signal(str)

    def __init__(self, fastapi_manager) -> None:
        super().__init__()
        self._fastapi_manager = fastapi_manager

    def run(self) -> None:
        """Wywoływane w QThread."""
        try:
            success = self._fastapi_manager.start()
            self.finished.emit(success)
        except Exception as exc:
            self.error.emit(str(exc))


class OpenVINOStartWorker(QObject):
    """Worker uruchamiający OpenVINO w tle (nie blokuje GUI)."""

    finished = Signal(bool)  # success
    base_url_ready = Signal(str)  # base_url po sukcesie
    error = Signal(str)

    def __init__(self, ov_backend) -> None:
        super().__init__()
        self._ov_backend = ov_backend

    def run(self) -> None:
        """Wywoływane w QThread."""
        try:
            success = self._ov_backend.load_model()
            if success:
                self.base_url_ready.emit(self._ov_backend.base_url)
            self.finished.emit(success)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# BackendManager
# ---------------------------------------------------------------------------

class BackendManager(QObject):
    """Zarządza wyborem backendu tłumaczenia.

    Dziedziczy po QObject dla komunikacji z GUI przez sygnały Qt.
    Wzorzec: wstrzyknięcie zależności — ServerManager jest dostarczany
    z MainWindow (nie tworzony wewnętrznie), bo MainWindow zarządza
    jego cyklem życia.

    Sygnały:
        backend_started(str): Emitowany po uruchomieniu backendu (base_url).
        backend_stopped(): Emitowany po zatrzymaniu backendu.
        backend_error(str): Emitowany przy błędzie (komunikat).
        operation_finished(): Emitowany po zakończeniu operacji.
    """

    # Sygnały Qt dla GUI
    backend_started = Signal(str)
    backend_stopped = Signal()
    backend_error = Signal(str)
    operation_finished = Signal()
    backend_loading = Signal(str)  # nazwa backendu — GUI blokuje przełączanie

    def __init__(self, config: Optional[BackendConfig] = None) -> None:
        super().__init__()
        self._config = config or BackendConfig()
        self._config.validate()

        self._server_manager: Optional[ServerManager] = None
        self._fastapi_manager: Optional["FastAPIServerManager"] = None
        self._openvino_backend = None  # lazy init przez _get_openvino_backend()
        self._last_error = ""

        # Thread/worker dla FastAPI start (G5 fix)
        self._fastapi_start_thread: Optional[QThread] = None
        self._fastapi_start_worker: Optional[FastAPIStartWorker] = None
        # Thread/worker dla OpenVINO start
        self._openvino_start_thread: Optional[QThread] = None
        self._openvino_start_worker: Optional[OpenVINOStartWorker] = None
        self._server_signals_connected = False

        # Lazy import — unikamy cyklicznych importów
        self._init_fastapi_manager()

    # ------------------------------------------------------------------
    # Inicjalizacja
    # ------------------------------------------------------------------

    def _init_fastapi_manager(self) -> None:
        """Inicjalizuj FastAPIServerManager.

        Lazy import żeby uniknąć problemów z zależnościami
        (transformers/torch mogą nie być zainstalowane).
        """
        try:
            from ..fastapi_manager import (
                FastAPIServerManager,
                FastAPIServerManagerConfig,
            )
            fastapi_config = FastAPIServerManagerConfig(
                model_path=self._config.fastapi_model_path,
                host=self._config.fastapi_host,
                port=self._config.fastapi_port,
                device=self._config.fastapi_device,
                dtype=self._config.fastapi_dtype,
            )
            self._fastapi_manager = FastAPIServerManager(fastapi_config)
        except ImportError:
            logger.warning(
                "FastAPIServerManager niedostępny — "
                "brak zależności (transformers/torch). "
                "Zainstaluj: pip install -r requirements-fastapi.txt"
            )
            self._fastapi_manager = None

    def _get_openvino_backend(self):
        """Lazy initialization OpenVINOBackend.

        Returns:
            Instancja OpenVINOBackend lub None jeśli niedostępny.
        """
        if self._openvino_backend is None:
            BackendClass, ConfigClass = _get_openvino_classes()
            if BackendClass is None or ConfigClass is None:
                return None
            try:
                ov_config = ConfigClass(
                    model_path=self._config.openvino_model_path,
                    device=self._config.openvino_device,
                )
                self._openvino_backend = BackendClass(ov_config)
            except Exception as exc:
                logger.error("Błąd inicjalizacji OpenVINOBackend: %s", exc)
                return None
        return self._openvino_backend

    def set_server_manager(self, server_manager: ServerManager) -> None:
        """Ustaw ServerManager z MainWindow (wstrzyknięcie zależności).

        Args:
            server_manager: Istniejący ServerManager z MainWindow.
        """
        self._server_manager = server_manager
        self._connect_server_signals()
        logger.info("ServerManager wstrzyknięty do BackendManager")

    def _connect_server_signals(self) -> None:
        """Podłącz sygnały ServerManager do sygnałów BackendManager."""
        if self._server_manager is None:
            return
        # Rozłącz poprzednie połączenia tylko jeśli były połączone
        if self._server_signals_connected:
            self._server_manager.server_started.disconnect(self.backend_started)
            self._server_manager.server_stopped.disconnect(self.backend_stopped)
            self._server_manager.server_error.disconnect(self._on_server_error)
            self._server_manager.operation_finished.disconnect(self.operation_finished)
        self._server_manager.server_started.connect(self.backend_started)
        self._server_manager.server_stopped.connect(self.backend_stopped)
        self._server_manager.server_error.connect(self._on_server_error)
        self._server_manager.operation_finished.connect(self.operation_finished)
        self._server_signals_connected = True

    def _on_server_error(self, message: str) -> None:
        """Obsługa błędu z ServerManager — zapamiętuje i propaguje."""
        self._last_error = message
        self.backend_error.emit(message)

    # ------------------------------------------------------------------
    # Właściwości
    # ------------------------------------------------------------------

    @property
    def config(self) -> BackendConfig:
        """Konfiguracja backendu."""
        return self._config

    # ------------------------------------------------------------------
    # Zarządzanie backendem
    # ------------------------------------------------------------------

    def get_active_backend(self) -> str:
        """Zwraca aktywny backend.

        Returns:
            'llama', 'cloud' lub 'fastapi'.
        """
        return self._config.backend_type

    def set_active_backend(self, backend_type: str) -> None:
        """Zmienia aktywny backend.

        Zatrzymuje obecny backend jeśli działa, następnie przełącza
        na nowy.

        Args:
            backend_type: 'llama', 'cloud' lub 'fastapi'.

        Raises:
            ValueError: Jeśli backend_type jest nieznany.
        """
        if backend_type not in BackendConfig._VALID_BACKENDS:
            raise ValueError(
                f"Nieznany backend: {backend_type!r}. "
                f"Dozwolone: {BackendConfig._VALID_BACKENDS}"
            )

        # Zatrzymaj obecny backend jeśli działa
        if self.is_running():
            self.stop()

        self._config.backend_type = backend_type
        logger.info("Zmieniono backend na: %s", backend_type)

    # ------------------------------------------------------------------
    # Cykl życia
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Uruchamia aktywny backend.

        Deleguje do odpowiedniego managera w zależności od backend_type.
        Dla Cloud emituje backend_started natychmiast (nie wymaga startu).
        """
        backend = self.get_active_backend()
        self._last_error = ""

        if backend == "llama":
            self._start_llama()
        elif backend == "fastapi":
            self._start_fastapi()
        elif backend == "openvino":
            self._start_openvino()
        elif backend == "cloud":
            self._start_cloud()

    def _start_llama(self) -> None:
        """Uruchom llama.cpp przez ServerManager."""
        if self._server_manager is None:
            self._last_error = "ServerManager nie jest ustawiony"
            self.backend_error.emit(self._last_error)
            return
        self._server_manager.start()

    def _start_fastapi(self) -> None:
        """Uruchom FastAPI przez FastAPIServerManager w QThread (nie blokuje GUI)."""
        if self._fastapi_manager is None:
            self._last_error = (
                "FastAPIServerManager niedostępny. "
                "Zainstaluj zależności: pip install -r requirements-fastapi.txt"
            )
            self.backend_error.emit(self._last_error)
            return

        # Sprawdź czy już jest thread startowy (bezpieczne sprawdzenie)
        if self._fastapi_start_thread is not None:
            try:
                if self._fastapi_start_thread.isRunning():
                    logger.warning("FastAPI start already in progress")
                    return
            except RuntimeError:
                # Thread już usunięty - wyczyść referencję
                self._fastapi_start_thread = None
                self._fastapi_start_worker = None

        # Zatrzymaj serwer jeśli działa (dla restartu)
        if self._fastapi_manager.is_running:
            self._fastapi_manager.stop()
            import time
            time.sleep(0.5)

        # Utwórz worker i thread
        worker = FastAPIStartWorker(self._fastapi_manager)
        thread = QThread()
        worker.moveToThread(thread)

        # Połącz sygnały
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_fastapi_start_finished)
        worker.error.connect(self._on_fastapi_start_error)

        # Cleanup thread po zakończeniu
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Zachowaj referencję
        self._fastapi_start_thread = thread
        self._fastapi_start_worker = worker

        # Uruchom thread
        self.backend_loading.emit("FastAPI (TranslateGemma)")
        thread.start()
        logger.info("FastAPI start thread started")

    def _on_fastapi_start_finished(self, success: bool) -> None:
        """Callback po zakończeniu FastAPI start."""
        logger.info(f"_on_fastapi_start_finished: success={success}")
        if success:
            base_url = self._fastapi_manager.base_url
            logger.info(f"_on_fastapi_start_finished: emitting backend_started with {base_url}")
            self.backend_started.emit(base_url)
        else:
            self._last_error = self._fastapi_manager.get_last_error()
            self.backend_error.emit(self._last_error)

    def _on_fastapi_start_error(self, error: str) -> None:
        """Callback po błędzie FastAPI start."""
        self._last_error = f"Błąd uruchamiania FastAPI: {error}"
        self.backend_error.emit(self._last_error)

    def _start_cloud(self) -> None:
        """Cloud nie wymaga startowania — emituj sygnał natychmiast."""
        if not self._config.cloud_base_url:
            self._last_error = "Brak cloud_base_url w konfiguracji"
            self.backend_error.emit(self._last_error)
            return
        self.backend_started.emit(self._config.cloud_base_url)

    def _start_openvino(self) -> None:
        """Uruchom backend OpenVINO w QThread (nie blokuje GUI)."""
        ov_backend = self._get_openvino_backend()
        if ov_backend is None:
            self._last_error = (
                "OpenVINOBackend niedostępny. "
                "Zainstaluj: pip install openvino openvino-genai"
            )
            self.backend_error.emit(self._last_error)
            return

        self.backend_loading.emit("OpenVINO")

        # Utwórz worker i thread
        worker = OpenVINOStartWorker(ov_backend)
        thread = QThread()
        worker.moveToThread(thread)

        # Połącz sygnały
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_openvino_start_finished)
        worker.base_url_ready.connect(self._on_openvino_base_url_ready)
        worker.error.connect(self._on_openvino_start_error)

        # Cleanup thread po zakończeniu
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Zachowaj referencję
        self._openvino_start_thread = thread
        self._openvino_start_worker = worker

        # Uruchom thread
        thread.start()
        logger.info("OpenVINO start thread started")

    def _on_openvino_base_url_ready(self, base_url: str) -> None:
        """Callback: OpenVINO załadowany, emituj backend_started."""
        self.backend_started.emit(base_url)

    def _on_openvino_start_finished(self, success: bool) -> None:
        """Callback po zakończeniu OpenVINO start."""
        if not success:
            self._last_error = self._openvino_backend.get_last_error() if self._openvino_backend else "OpenVINO load failed"

    def _on_openvino_start_error(self, error: str) -> None:
        """Callback po błędzie OpenVINO start."""
        self._last_error = f"Błąd ładowania modelu OpenVINO: {error}"
        self.backend_error.emit(self._last_error)

    def stop(self) -> None:
        """Zatrzymuje aktywny backend."""
        backend = self.get_active_backend()

        if backend == "llama":
            if self._server_manager is not None:
                self._server_manager.stop()
        elif backend == "fastapi":
            if self._fastapi_manager is not None:
                self._fastapi_manager.stop()
                self.backend_stopped.emit()
        elif backend == "openvino":
            if self._openvino_backend is not None:
                self._openvino_backend.unload_model()
                self.backend_stopped.emit()
        # Cloud nie wymaga zatrzymywania

    def stop_llama(self) -> None:
        """Zatrzymaj serwer llama.cpp (niezależnie od aktywnego backendu)."""
        if self._server_manager is not None and self._server_manager.is_running:
            self._server_manager.stop()

    def stop_fastapi(self) -> None:
        """Zatrzymaj serwer FastAPI (niezależnie od aktywnego backendu)."""
        if self._fastapi_manager is not None and self._fastapi_manager.is_running:
            self._fastapi_manager.stop()
            self.backend_stopped.emit()

    def stop_openvino(self) -> None:
        """Zatrzymaj backend OpenVINO (niezależnie od aktywnego backendu)."""
        if self._openvino_backend is not None and self._openvino_backend.is_loaded:
            self._openvino_backend.unload_model()
            self.backend_stopped.emit()

    def restart(self, config_updates: Optional[dict] = None, backend: Optional[str] = None) -> None:
        """Restartuje aktywny backend.

        Deleguje do odpowiedniego managera żeby uniknąć race condition
        (stop jest asynchroniczny, start nie może być wywołany przed zakończeniem stop).

        Args:
            config_updates: Słownik z aktualizacjami konfiguracji.
            backend: Backend do restartu (jeśli None, użyj get_active_backend()).
        """
        # Użyj podanego backendu lub pobierz aktywny
        if backend is None:
            backend = self.get_active_backend()

        if backend == "cloud":
            return  # Cloud nie wymaga restartu

        if backend == "llama":
            # ServerManager.restart() obsługuje to poprawnie (RestartWorker)
            if self._server_manager is not None:
                self._server_manager.restart(config_updates or {})
        elif backend == "fastapi":
            # FastAPIServerManager.restart() - użyj thread żeby nie blokować GUI
            if self._fastapi_manager is not None and config_updates:
                # Zaktualizuj konfigurację przed restartem
                from ..fastapi_manager import FastAPIServerManagerConfig
                new_config = FastAPIServerManagerConfig(
                    host=self._fastapi_manager._config.host,
                    port=config_updates.get("port", self._fastapi_manager._config.port),
                    model_path=config_updates.get("model_path", self._fastapi_manager._config.model_path),
                    device=self._fastapi_manager._config.device,
                    dtype=config_updates.get("dtype", self._fastapi_manager._config.dtype),
                )
                self._fastapi_manager.update_config(new_config)
            # Użyj FastAPIStartWorker dla restartu (nie blokuje GUI)
            self._start_fastapi()
        elif backend == "openvino":
            # OpenVINO - zatrzymaj i uruchom ponownie
            if self._openvino_backend is not None:
                self._openvino_backend.unload_model()
                if config_updates and "model_path" in config_updates:
                    self._openvino_backend._config.model_path = config_updates["model_path"]
                if config_updates and "device" in config_updates:
                    self._openvino_backend._config.device = config_updates["device"]
                success = self._openvino_backend.load_model()
                if success:
                    self.backend_started.emit(self._openvino_backend.base_url)
                # Emituj operation_finished po zakończeniu
                self.operation_finished.emit()

    # ------------------------------------------------------------------
    # Stan
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        """Sprawdza czy aktywny backend działa.

        Returns:
            True jeśli backend jest uruchomiony.
        """
        backend = self.get_active_backend()

        if backend == "llama":
            return (
                self._server_manager is not None
                and self._server_manager.is_running
            )
        elif backend == "fastapi":
            return (
                self._fastapi_manager is not None
                and self._fastapi_manager.is_running
            )
        elif backend == "openvino":
            return (
                self._openvino_backend is not None
                and self._openvino_backend.is_loaded
            )
        elif backend == "cloud":
            return True  # Cloud zawsze "działa"

        return False

    def get_base_url(self) -> str:
        """Zwraca URL API aktywnego backendu.

        Returns:
            URL endpointu API lub pusty string.
        """
        backend = self.get_active_backend()

        if backend == "llama":
            # ServerManager nie ma base_url — odczytujemy przez server.config
            if (
                self._server_manager is not None
                and self._server_manager.server is not None
            ):
                return self._server_manager.server.config.base_url
            # Fallback: odczytaj z konfiguracji jeśli serwer nie jest jeszcze utworzony
            if (
                self._server_manager is not None
                and self._server_manager.config is not None
            ):
                return self._server_manager.config.base_url
            return ""
        elif backend == "fastapi":
            if self._fastapi_manager is not None:
                return self._fastapi_manager.base_url
            return ""
        elif backend == "openvino":
            if self._openvino_backend is not None:
                return self._openvino_backend.base_url
            return ""
        elif backend == "cloud":
            return self._config.cloud_base_url

        return ""

    def get_last_error(self) -> str:
        """Zwraca ostatni błąd aktywnego backendu.

        Returns:
            Komunikat błędu lub pusty string.
        """
        backend = self.get_active_backend()

        if backend == "fastapi":
            if self._fastapi_manager is not None:
                return self._fastapi_manager.get_last_error()

        # Dla llama i cloud — zwracamy zapamiętany błąd z _on_server_error
        return self._last_error
