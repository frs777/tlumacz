"""Persistent configuration for the Tłumacz GUI.

Settings are stored as JSON in ``~/.config/tlumacz/config.json`` so
the application works when installed globally (AUR) and per-user.

Loading is defensive: a missing file is a normal first run, but a file that
cannot be parsed, is not a JSON object, contains unknown keys, or holds
values of the wrong type is repaired by falling back to defaults for the
affected fields. Any such problem is reported via :func:`load_settings`,
which returns a human-readable warning for the GUI to surface.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

APP_NAME = "tlumacz"

_INT_FIELDS = {"chunk_size", "server_port"}
_FLOAT_FIELDS = {"temperature"}
_BOOL_FIELDS = {"auto_start_server"}
_LIST_FIELDS = {"enabled_skills"}


def config_dir() -> Path:
    """Return the per-user config directory (XDG_CONFIG_HOME aware)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / APP_NAME


@dataclass
class AppSettings:
    """GUI settings persisted to disk."""

    base_url: str = "http://127.0.0.1:8080/v1"
    api_key: str = "ollama"
    model: str = "qwen2.5-coder-7b-instruct-q5_k_m"
    chunk_size: int = 4000
    temperature: float = 0.1
    target_language: str = "Polish"
    theme: str = "system"
    glossary_path: str = ""
    system_prompt: str = ""
    enabled_skills: list[str] = field(default_factory=list)
    server_port: int = 18080
    server_gguf_path: str = ""
    auto_start_server: bool = False
    last_input: str = ""
    last_output: str = ""

    @classmethod
    def from_dict(
        cls, data: Any
    ) -> tuple["AppSettings", list[str]]:
        """Build settings from a decoded JSON value.

        Returns ``(settings, problems)``. ``problems`` lists every issue
        found (unknown keys, wrong-typed values); affected fields keep their
        defaults while valid fields are preserved. A non-dict ``data`` yields
        all-default settings with a single problem.
        """
        problems: list[str] = []
        if not isinstance(data, dict):
            return cls(), ["Plik konfiguracji nie jest obiektem JSON."]

        unknown = sorted(
            key for key in data if key not in cls.__dataclass_fields__
        )
        if unknown:
            problems.append("Nieznane pola: " + ", ".join(unknown))

        values: dict[str, Any] = {}
        for name in cls.__dataclass_fields__:
            if name not in data:
                continue
            value = data[name]
            if _valid_value(name, value):
                values[name] = value
            else:
                problems.append(f"Pole „{name}” ma nieprawidłowy typ.")
        return cls(**values), problems


def load_settings() -> tuple[AppSettings, Optional[str]]:
    """Load settings from disk.

    Returns ``(settings, warning)`` where ``warning`` is ``None`` on a clean
    load (including a missing file, which is a normal first run) and a
    human-readable message otherwise.
    """
    path = config_dir() / "config.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return AppSettings(), None
    except (OSError, ValueError) as exc:
        return (
            AppSettings(),
            f"Nie można odczytać konfiguracji: {exc}. "
            "Użyto ustawień domyślnych.",
        )

    settings, problems = AppSettings.from_dict(data)
    if problems:
        return settings, (
            "Wykryto problemy w konfiguracji: " + "; ".join(problems)
            + " Użyto wartości domyślnych dla błędnych pól."
        )
    return settings, None


def save_settings(settings: AppSettings) -> None:
    """Persist settings to disk, creating the config directory if needed."""
    path = config_dir() / "config.json"
    config_dir().mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=2)
    tmp.replace(path)


def _valid_value(name: str, value: Any) -> bool:
    """Return whether ``value`` is acceptable for the field ``name``."""
    if name in _INT_FIELDS:
        return isinstance(value, int) and not isinstance(value, bool)
    if name in _FLOAT_FIELDS:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name in _BOOL_FIELDS:
        return isinstance(value, bool)
    if name in _LIST_FIELDS:
        return isinstance(value, list) and all(
            isinstance(item, str) for item in value
        )
    return isinstance(value, str)