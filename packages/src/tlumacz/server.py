"""Managed llama-server process for Tłumacz.

The GUI can start its own local llama.cpp server on a dedicated port so the
user does not need to run a server manually. The process is started when the
app launches and stopped when it exits.

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import signal
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


SERVER_MODEL_ALIAS = "local"
"""Model name used in OpenAI requests against the managed server.

The managed llama-server is always started with ``--alias local``, so API
requests must address the model as ``local`` regardless of the GGUF file.
"""


class ServerStartError(Exception):
    """Raised when the llama-server process cannot be started or probed."""


@dataclass
class ServerConfig:
    """Configuration for the managed llama-server process."""

    host: str = "127.0.0.1"
    port: int = 18080
    gguf_path: str = ""
    ctx_size: int = 8192
    parallel: int = 1
    compute_mode: str = "gpu"
    chat_template: str = ""
    extra_args: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.extra_args is None:
            self.extra_args = []
        if self.parallel < 1:
            self.parallel = 1
        if self.compute_mode not in {"gpu", "cpu"}:
            self.compute_mode = "gpu"

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}/v1"

    def effective_ctx_size(self, chunk_size: int = 4000) -> int:
        """Return a context size large enough for ``parallel`` slots.

        Each slot must hold the system prompt plus a chunk. A rough rule is
        ``chunk_size // 3`` tokens for the chunk plus a 2048-token margin.
        The result is at least the configured ``ctx_size``.
        """
        tokens_per_slot = max(4096, chunk_size // 3 + 2048)
        return max(self.ctx_size, self.parallel * tokens_per_slot)


class LlamaServer:
    """Spawn and supervise a local llama-server subprocess."""

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._last_error = ""

    def is_running(self) -> bool:
        """Return ``True`` if an OpenAI-compatible endpoint responds on our port."""
        url = f"{self.config.base_url}/models"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                result = resp.status == 200
                logger.debug(f"is_running() -> {result} (status={resp.status})")
                return result
        except (OSError, ValueError) as e:
            logger.debug(f"is_running() -> False (exception: {type(e).__name__}: {e})")
            return False

    def start(self) -> Optional[str]:
        """Start llama-server, retrying with fallback templates if needed.

        Returns the chat template that worked (``None`` = native jinja), so
        the caller can remember it for the model. Raises :class:`ServerStartError`
        when every candidate fails.
        """
        logger.info(f"start() called, _process={self._process}, port={self.config.port}")
        binary = shutil.which("llama-server")
        if binary is None:
            raise ServerStartError(
                "Nie znaleziono 'llama-server' w PATH. Zainstaluj llama.cpp "
                "(np. paczka 'llama.cpp-cuda' lub 'llama.cpp')."
            )
        if not self.config.gguf_path:
            raise ServerStartError("Brak ścieżki do pliku GGUF modelu.")
        if self._process is not None and self._process.poll() is None:
            raise ServerStartError("Serwer już działa (proces aktywny).")

        # Sprawdź czy port jest zajęty przez osierocony proces
        if self._is_port_busy():
            logger.info("start(): port is busy, killing occupier")
            self._kill_port_occupier()

        last_error = "nieznany błąd"
        for template in self._template_attempts():
            logger.info(f"Attempting to start llama-server with template={template}")
            self._process = subprocess.Popen(
                self._command(binary, template),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.info(f"Process started, PID={self._process.pid}")
            if self._wait_ready():
                logger.info(f"Server ready with template={template}")
                return template
            logger.warning(f"Server not ready with template={template}")
            if self._last_error:
                last_error = self._last_error

        self._process = None
        raise ServerStartError(
            f"Serwer nie uruchomił się: {last_error}."
        )

    def _command(
        self, binary: str, chat_template: Optional[str], chunk_size: int = 4000
    ) -> list[str]:
        """Build the llama-server command line for a chat template."""
        command = [
            binary,
            "-m",
            self.config.gguf_path,
            "--alias",
            "local",
            "--host",
            self.config.host,
            "--port",
            str(self.config.port),
            "--ctx-size",
            str(self.config.effective_ctx_size(chunk_size)),
            "--parallel",
            str(self.config.parallel),
        ]
        # GPU mode explicitly requests Vulkan offload. A high layer count lets
        # llama.cpp offload as much as the available VRAM can accommodate.
        if self.config.compute_mode == "cpu":
            command += ["--n-gpu-layers", "0"]
        else:
            command += ["--n-gpu-layers", "999", "--split-mode", "none"]
        if chat_template:
            command += ["--no-jinja", "--chat-template", chat_template]
        else:
            command.append("--jinja")
        command += list(self.config.extra_args)
        return command

    def _template_attempts(self) -> list[Optional[str]]:
        """Candidate chat templates in the order they should be tried.

        The configured value (or a remembered profile value passed by the
        caller) is tried first; the other candidates are tried as fallbacks.
        ``None`` means the model's native jinja template.
        
        Note: "translategemma" uses native Gemma 3 jinja template (None),
        but the prompt includes language codes (en, pl, de, etc.).
        """
        primary = self.config.chat_template or None
        # "translategemma" uses native jinja (Gemma 3 template)
        if primary == "translategemma":
            primary = None
        attempts = [primary]
        for candidate in ("chatml", None):
            if candidate != primary and candidate not in attempts:
                attempts.append(candidate)
        return attempts

    def _wait_ready(self) -> bool:
        """Wait until the server responds or the process dies.

        Returns ``True`` when the endpoint responds. On failure stores a
        human-readable reason in ``self._last_error`` and returns ``False``.
        """
        logger.info(f"_wait_ready() started, PID={self._process.pid if self._process else None}")
        self._last_error = ""
        deadline = time.monotonic() + 60.0
        attempt = 0
        while time.monotonic() < deadline:
            attempt += 1
            if self._process.poll() is not None:
                code = self._process.returncode
                logger.warning(f"_wait_ready(): process exited with code {code}")
                self._process = None
                self._last_error = (
                    f"llama-server zakończył się przedwcześnie (kod {code}). "
                    "Sprawdź ścieżkę GGUF i dane modelu."
                )
                return False
            if self.is_running():
                logger.info(f"_wait_ready(): server ready after {attempt} attempts")
                return True
            if attempt % 10 == 0:
                logger.debug(f"_wait_ready(): still waiting, attempt {attempt}")
            time.sleep(0.5)

        logger.error(f"_wait_ready(): timeout after {attempt} attempts")
        self.stop()
        self._last_error = (
            f"Serwer nie odpowiedział w ciągu 60 s na porcie {self.config.port}."
        )
        return False

    def stop(self) -> None:
        """Terminate the managed llama-server subprocess, if any."""
        logger.info(f"stop() called, _process={self._process}")
        if self._process is None:
            # Sprawdź czy serwer HTTP nadal odpowiada (proces z poprzedniej sesji)
            if self.is_running():
                logger.info("stop(): _process is None but server is running, killing by port")
                self._kill_by_port()
            else:
                logger.debug("stop(): _process is None and server not running, nothing to do")
            return
        if self._process.poll() is None:
            logger.info(f"stop(): terminating process PID={self._process.pid}")
            try:
                self._process.terminate()
                self._process.wait(timeout=10)
                logger.info(f"stop(): process terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"stop(): process did not terminate, killing")
                self._process.kill()
                self._process.wait(timeout=5)
                logger.info(f"stop(): process killed")
            except OSError as e:
                logger.error(f"stop(): OSError: {e}")
        else:
            logger.info(f"stop(): process already exited (returncode={self._process.returncode})")
        self._process = None
        # Sprawdź czy serwer HTTP nadal odpowiada (osierocony proces z innej sesji)
        if self.is_running():
            logger.info("stop(): server still running after process exit, killing by port")
            self._kill_by_port()
        logger.info("stop(): completed, _process set to None")

    def _kill_by_port(self) -> None:
        """Kill process listening on the server port (fallback for orphaned servers)."""
        port = self.config.port
        try:
            # Użyj ss lub lsof do znalezienia PID
            pid = None
            if shutil.which("ss"):
                result = subprocess.run(
                    ["ss", "-tlnp", f"sport = :{port}"],
                    capture_output=True, text=True, timeout=5
                )
                # ss output: "LISTEN 0 512 127.0.0.1:17580 0.0.0.0:* users:(("llama-server",pid=4416,fd=3))"
                for line in result.stdout.splitlines():
                    if "pid=" in line:
                        match = re.search(r"pid=(\d+)", line)
                        if match:
                            pid = int(match.group(1))
                            break
            elif shutil.which("lsof"):
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    pid = int(result.stdout.strip().split()[0])

            if pid:
                logger.info(f"_kill_by_port(): killing PID={pid}")
                try:
                    os.kill(pid, signal.SIGTERM)
                    # Poczekaj aż proces się zakończy
                    for _ in range(10):
                        time.sleep(1)
                        try:
                            os.kill(pid, 0)  # Sprawdź czy proces nadal istnieje
                        except OSError:
                            logger.info(f"_kill_by_port(): process {pid} terminated")
                            return
                    # Jeśli nadal działa, zabij
                    logger.warning(f"_kill_by_port(): process {pid} did not terminate, killing")
                    os.kill(pid, signal.SIGKILL)
                except OSError as e:
                    logger.error(f"_kill_by_port(): OSError: {e}")
            else:
                logger.warning(f"_kill_by_port(): no process found on port {port}")
        except Exception as e:
            logger.error(f"_kill_by_port(): failed: {type(e).__name__}: {e}")

    def _is_port_busy(self) -> bool:
        """Sprawdź czy port jest zajęty przez proces llama-server."""
        port = self.config.port
        try:
            if not shutil.which("ss"):
                return False
            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True, text=True, timeout=5
            )
            # Sprawdź czy jest proces na tym porcie
            for line in result.stdout.splitlines():
                if "pid=" in line and "llama-server" in line:
                    return True
            return False
        except Exception as e:
            logger.error(f"_is_port_busy(): failed: {type(e).__name__}: {e}")
            return False

    def _kill_port_occupier(self) -> None:
        """Zabij proces zajmujący port (osierocony llama-server)."""
        port = self.config.port
        try:
            if not shutil.which("ss"):
                return
            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "pid=" in line:
                    match = re.search(r"pid=(\d+)", line)
                    if match:
                        pid = int(match.group(1))
                        # Nie zabijaj naszego procesu
                        if self._process is not None and pid == self._process.pid:
                            continue
                        logger.info(f"_kill_port_occupier(): killing PID={pid}")
                        try:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(1)
                            try:
                                os.kill(pid, 0)  # Sprawdź czy nadal istnieje
                                os.kill(pid, signal.SIGKILL)
                            except OSError:
                                pass  # Proces się zakończył
                        except OSError as e:
                            logger.error(f"_kill_port_occupier(): OSError: {e}")
        except Exception as e:
            logger.error(f"_kill_port_occupier(): failed: {type(e).__name__}: {e}")