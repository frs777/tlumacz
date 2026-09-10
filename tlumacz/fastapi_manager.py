"""Manager serwera FastAPI + Transformers dla TranslateGemma.

Ten moduł zarządza cyklem życia serwera FastAPI który udostępnia
model TranslateGemma z obsługą specjalnego formatu z kodami języków.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

from .fastapi_server import FastAPIServerConfig, TranslateGemmaServer

logger = logging.getLogger(__name__)


@dataclass
class FastAPIServerManagerConfig:
    """Konfiguracja managera serwera FastAPI."""

    model_path: str = "google/translategemma-4b-it"
    host: str = "127.0.0.1"
    port: int = 8001
    device: str = "auto"
    dtype: str = "float16"
    auto_start: bool = False


class FastAPIServerManager:
    """Manager serwera FastAPI + Transformers.
    
    Zarządza cyklem życia serwera TranslateGemma:
    - Start/stop serwera
    - Health check
    - Stan serwera (IDLE/STARTING/RUNNING/STOPPING)
    """

    # Stany serwera
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"

    def __init__(self, config: Optional[FastAPIServerManagerConfig] = None) -> None:
        self._config = config or FastAPIServerManagerConfig()
        self._server: Optional[TranslateGemmaServer] = None
        self._state = self.IDLE
        self._lock = threading.Lock()
        self._last_error = ""

    @property
    def state(self) -> str:
        """Aktualny stan serwera."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Czy serwer działa."""
        return self._state == self.RUNNING and self._server is not None and self._server.is_running()

    @property
    def base_url(self) -> str:
        """URL serwera API."""
        return f"http://{self._config.host}:{self._config.port}/v1"

    def start(self) -> bool:
        """Uruchom serwer FastAPI.
        
        Returns:
            True jeśli serwer uruchomił się poprawnie, False w przeciwnym razie.
        """
        with self._lock:
            if self._state == self.RUNNING:
                logger.warning("Server already running")
                return True
            
            if self._state == self.STARTING:
                logger.warning("Server already starting")
                return False

            self._state = self.STARTING
            self._last_error = ""

        try:
            logger.info(f"Starting FastAPI server with model {self._config.model_path}")
            
            # Utwórz konfigurację serwera
            server_config = FastAPIServerConfig(
                model_path=self._config.model_path,
                host=self._config.host,
                port=self._config.port,
                device=self._config.device,
                dtype=self._config.dtype,
            )
            
            # Utwórz i uruchom serwer
            self._server = TranslateGemmaServer(server_config)
            self._server.start()
            
            # Poczekaj aż serwer będzie gotowy
            if self._wait_ready(timeout=120):
                with self._lock:
                    self._state = self.RUNNING
                logger.info(f"FastAPI server started on {self.base_url}")
                return True
            else:
                with self._lock:
                    self._state = self.IDLE
                    self._last_error = "Server not ready after timeout"
                logger.error("FastAPI server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting FastAPI server: {e}")
            with self._lock:
                self._state = self.IDLE
                self._last_error = str(e)
            return False

    def stop(self) -> None:
        """Zatrzymaj serwer FastAPI."""
        with self._lock:
            if self._state != self.RUNNING:
                logger.warning("Server not running")
                return
            self._state = self.STOPPING

        try:
            logger.info("Stopping FastAPI server")
            if self._server is not None:
                self._server.stop()
                self._server = None
            
            with self._lock:
                self._state = self.IDLE
            logger.info("FastAPI server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping FastAPI server: {e}")
            with self._lock:
                self._state = self.IDLE

    def restart(self) -> bool:
        """Restart serwera (stop + start)."""
        logger.info("Restarting FastAPI server")
        self.stop()
        time.sleep(1)
        return self.start()

    def _wait_ready(self, timeout: float = 120) -> bool:
        """Poczekaj aż serwer będzie gotowy.
        
        Args:
            timeout: Maksymalny czas oczekiwania w sekundach
            
        Returns:
            True jeśli serwer jest gotowy, False jeśli timeout
        """
        deadline = time.monotonic() + timeout
        attempt = 0
        
        while time.monotonic() < deadline:
            attempt += 1
            
            if self._server is not None and self._server.is_running():
                # Sprawdź health endpoint
                if self._health_check():
                    logger.info(f"Server ready after {attempt} attempts")
                    return True
            
            time.sleep(0.5)
        
        logger.error(f"Server not ready after {attempt} attempts (timeout={timeout}s)")
        return False

    def _health_check(self) -> bool:
        """Sprawdź czy serwer odpowiada."""
        url = f"http://{self._config.host}:{self._config.port}/health"
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def get_last_error(self) -> str:
        """Pobierz ostatni błąd."""
        return self._last_error

    def update_config(self, config: FastAPIServerManagerConfig) -> None:
        """Zaktualizuj konfigurację (wymaga restartu)."""
        was_running = self.is_running
        if was_running:
            self.stop()
        
        self._config = config
        
        if was_running:
            self.start()
