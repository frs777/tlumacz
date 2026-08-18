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


class ServerStartError(Exception):
    """Raised when the llama-server process cannot be started or probed."""


@dataclass
class ServerConfig:
    """Configuration for the managed llama-server process."""

    host: str = "127.0.0.1"
    port: int = 18080
    gguf_path: str = ""
    ctx_size: int = 4096
    parallel: int = 1
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

    def is_running(self) -> bool:
        """Return ``True`` if an OpenAI-compatible endpoint responds on our port."""
        url = f"{self.config.base_url}/models"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                return resp.status == 200
        except (OSError, ValueError):
            return False

    def start(self) -> None:
        """Start llama-server in the background and wait until it responds."""
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
        ] + list(self.config.extra_args)

        self._process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                self._process = None
                raise ServerStartError(
                    f"llama-server zakończył się przedwcześnie (kod "
                    f"{self._process.returncode if self._process else '?'}). "
                    "Sprawdź ścieżkę GGUF i dane modelu."
                )
            if self.is_running():
                return
            time.sleep(0.5)

        self.stop()
        raise ServerStartError(
            f"Serwer nie odpowiedział w ciągu 60 s na porcie {self.config.port}."
        )

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