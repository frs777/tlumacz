"""Application entry point for the Tłumacz Qt GUI.

Run with::

    python -m tlumacz.qt_gui.app
    tlumacz
"""

from __future__ import annotations

import atexit
import signal
import sys

from PySide6.QtWidgets import QApplication

from ..server import LlamaServer, ServerConfig, ServerStartError
from .config import load_settings
from .main_window import MainWindow
from .theme import apply_theme


def main() -> int:
    settings, config_warning = load_settings()
    if config_warning:
        print(f"UWAGA (konfiguracja): {config_warning}", file=sys.stderr)

    server: LlamaServer | None = None
    if settings.auto_start_server:
        server = LlamaServer(
            ServerConfig(
                port=settings.server_port,
                gguf_path=settings.server_gguf_path,
            )
        )
        try:
            server.start()
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
