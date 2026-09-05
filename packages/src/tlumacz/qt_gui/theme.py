"""Theme handling for the Tłumacz GUI.

Supports three modes: ``system`` (follow the OS color scheme), ``light``
and ``dark``. Stylesheets live in the bundled ``resources`` package and
are named ``style_<theme>.qss``.
"""

from __future__ import annotations

from importlib import resources

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

THEMES = ("system", "light", "dark")


def resolve_theme(mode: str, app: QApplication) -> str:
    """Return ``light`` or ``dark`` for the given mode."""
    if mode == "light":
        return "light"
    if mode == "dark":
        return "dark"
    scheme = app.styleHints().colorScheme()
    return "dark" if scheme == Qt.ColorScheme.Dark else "light"


def load_stylesheet(theme: str) -> str:
    """Load the QSS for a resolved theme (``light`` or ``dark``)."""
    name = f"style_{theme}.qss"
    qss = resources.files("tlumacz.qt_gui.resources").joinpath(name)
    with qss.open("r", encoding="utf-8") as f:
        return f.read()


def apply_theme(app: QApplication, mode: str) -> None:
    """Apply the stylesheet for ``mode`` (``system``/``light``/``dark``)."""
    try:
        app.setStyleSheet(load_stylesheet(resolve_theme(mode, app)))
    except (OSError, ModuleNotFoundError):
        # Styling is cosmetic; fall back to the platform default if missing.
        app.setStyleSheet("")
