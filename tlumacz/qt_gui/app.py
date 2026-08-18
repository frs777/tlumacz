"""Application entry point for the Tłumacz Qt GUI.

Run with::

    python -m tlumacz.qt_gui.app
    tlumacz
"""

from __future__ import annotations

import sys
from importlib import resources

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def _load_stylesheet(app: QApplication) -> None:
    """Load the bundled QSS stylesheet from package resources."""
    try:
        qss = resources.files("tlumacz.qt_gui.resources").joinpath("style.qss")
        with qss.open("r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except (OSError, ModuleNotFoundError):
        # Styling is cosmetic; keep going if the file is missing.
        pass


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Tłumacz")
    app.setApplicationDisplayName("Tłumacz")
    app.setDesktopFileName("tlumacz")

    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
