"""Managed llama-server process for Tłumacz.

The GUI can start its own local llama.cpp server on a dedicated port so the
user does not need to run a server manually. The process is started when the
app launches and stopped when it exits.

This module is intentionally free of Qt dependencies.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional


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
    chat_template: str = ""
    extra_args: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.extra_args is None:
            self.extra_args = []

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}/v1"


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
                return resp.status == 200
        except (OSError, ValueError):
            return False

    def start(self) -> Optional[str]:
        """Start llama-server, retrying with fallback templates if needed.

        Returns the chat template that worked (``None`` = native jinja), so
        the caller can remember it for the model. Raises :class:`ServerStartError`
        when every candidate fails.
        """
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

        last_error = "nieznany błąd"
        for template in self._template_attempts():
            self._process = subprocess.Popen(
                self._command(binary, template),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            if self._wait_ready():
                return template
            if self._last_error:
                last_error = self._last_error

        self._process = None
        raise ServerStartError(
            f"Serwer nie uruchomił się: {last_error}."
        )

    def _command(self, binary: str, chat_template: Optional[str]) -> list[str]:
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
            str(self.config.ctx_size),
            "--parallel",
            str(self.config.parallel),
        ]
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
        """
        primary = self.config.chat_template or None
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
        self._last_error = ""
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                code = self._process.returncode
                self._process = None
                self._last_error = (
                    f"llama-server zakończył się przedwcześnie (kod {code}). "
                    "Sprawdź ścieżkę GGUF i dane modelu."
                )
                return False
            if self.is_running():
                return True
            time.sleep(0.5)

        self.stop()
        self._last_error = (
            f"Serwer nie odpowiedział w ciągu 60 s na porcie {self.config.port}."
        )
        return False

    def stop(self) -> None:
        """Terminate the managed llama-server subprocess, if any."""
        if self._process is None:
            return
        if self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
            except OSError:
                pass
        self._process = None