"""Application entry point for the Agent Translator Qt GUI.

Run with::

    python -m agent_translator.qt_gui.app
    agent-translator
"""

from __future__ import annotations

import sys
from importlib import resources

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def _load_stylesheet(app: QApplication) -> None:
    """Load the bundled QSS stylesheet from package resources."""
    try:
        qss = resources.files("agent_translator.qt_gui.resources").joinpath("style.qss")
        with qss.open("r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except (OSError, ModuleNotFoundError):
        # Styling is cosmetic; keep going if the file is missing.
        pass


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Translator")
    app.setApplicationDisplayName("Agent Translator")
    app.setDesktopFileName("agent-translator")

    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
