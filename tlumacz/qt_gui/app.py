"""Application entry point for the Tłumacz Qt GUI.

Run with::

    python -m tlumacz.qt_gui.app
    tlumacz
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ..server import LlamaServer, ServerConfig, ServerStartError
from .config import load_settings, save_settings
from .main_window import MainWindow
from .theme import apply_theme


def main() -> int:
    # Configure logging for debugging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

    # Ustaw HF_TOKEN ze zmiennej środowiskowej (fallback z ~/.bashrc)
    if not os.environ.get("HF_TOKEN"):
        bashrc = Path.home() / ".bashrc"
        if bashrc.exists():
            with open(bashrc, "r") as f:
                for line in f:
                    if line.startswith("export HF_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        os.environ["HF_TOKEN"] = token
                        logging.info("HF_TOKEN loaded from ~/.bashrc")
                        break
    
    settings, config_warning = load_settings()
    if config_warning:
        print(f"UWAGA (konfiguracja): {config_warning}", file=sys.stderr)

    server: LlamaServer | None = None
    # Uruchom llama-server TYLKO gdy backend_type to "llama"
    if settings.auto_start_server and settings.backend_type == "llama" and settings.server_gguf_path:
        profile = settings.model_profiles.get(settings.server_gguf_path, {})
        chat_template = settings.server_chat_template or profile.get(
            "chat_template", ""
        )
        server = LlamaServer(
            ServerConfig(
                port=settings.server_port,
                parallel=settings.server_parallel,
                compute_mode=settings.server_compute_mode,
                gguf_path=settings.server_gguf_path,
                chat_template=chat_template,
            )
        )
        try:
            worked = server.start()
            if worked and worked != settings.server_chat_template:
                settings.model_profiles[settings.server_gguf_path] = {
                    "chat_template": worked
                }
                save_settings(settings)
            atexit.register(server.stop)
        except ServerStartError as exc:
            print(f"Nie udało się uruchomić serwera: {exc}", file=sys.stderr)
            server = None

    app = QApplication(sys.argv)
    app.setApplicationName("Tłumacz")
    app.setApplicationDisplayName("Tłumacz")
    app.setDesktopFileName("tlumacz")

    apply_theme(app, settings.theme)

    def _handle_signal(signum: int, _frame: object) -> None:
        """Gracefully quit the Qt loop so the managed server is stopped."""
        app.quit()

    if server is not None:
        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

    window = MainWindow(server=server)

    def _on_system_color_scheme_changed() -> None:
        """Re-apply the theme when the OS color scheme changes (system mode)."""
        if window.theme_mode() == "system":
            apply_theme(app, "system")

    app.styleHints().colorSchemeChanged.connect(_on_system_color_scheme_changed)

    window.show()
    rc = app.exec()

    if server is not None:
        server.stop()
    return rc


if __name__ == "__main__":
    sys.exit(main())
