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
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..preprocess import DEFAULT_SKIP_PATTERNS

APP_NAME = "tlumacz"

_INT_FIELDS = {"chunk_size", "server_port", "server_parallel"}
_FLOAT_FIELDS = {"temperature"}
_BOOL_FIELDS = {"auto_start_server", "cache_clear_after_translation"}
_LIST_FIELDS = {"enabled_skills", "skip_line_patterns", "cloud_models"}
_DICT_FIELDS = {"model_profiles"}


def config_dir() -> Path:
    """Return the per-user config directory (XDG_CONFIG_HOME aware)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / APP_NAME


def _load_cloud_models_config() -> list[dict[str, str]]:
    """Load cloud models configuration from cloud_models.json.

    Returns list of cloud model definitions with name, base_url, api_key, description.
    Falls back to empty list if file is missing or invalid.
    """
    # Najpierw sprawdź w katalogu projektu (dla dewelopera)
    project_config = Path(__file__).parent.parent.parent / "cloud_models.json"
    if project_config.is_file():
        try:
            with open(project_config, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("cloud_models", [])
        except (OSError, ValueError):
            pass

    # Potem sprawdź w katalogu konfiguracyjnym użytkownika
    user_config = config_dir() / "cloud_models.json"
    if user_config.is_file():
        try:
            with open(user_config, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("cloud_models", [])
        except (OSError, ValueError):
            pass

    # Domyślna konfiguracja
    return [
        {
            "name": "gemini-3.5-flash",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": "",
            "description": "Google Gemini 3.5 Flash - szybki model chmurowy",
        },
        {
            "name": "gemini-3.5-flash-lite",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": "",
            "description": "Google Gemini 3.5 Flash Lite - najszybszy, prawie nieograniczony (60 RPM)",
        },
    ]


# Załaduj konfigurację cloud models przy imporcie
CLOUD_MODELS_CONFIG = _load_cloud_models_config()


@dataclass
class AppSettings:
    """GUI settings persisted to disk."""

    base_url: str = "http://127.0.0.1:8080/v1"
    api_key: str = "ollama"
    model: str = "LOCAL"  # LOCAL, nazwa cloud model, lub własny model
    chunk_size: int = 4000
    temperature: float = 0.1
    target_language: str = "Polish"
    theme: str = "system"
    glossary_path: str = ""
    system_prompt: str = ""
    enabled_skills: list[str] = field(default_factory=list)
    skip_line_patterns: list[str] = field(
        default_factory=lambda: list(DEFAULT_SKIP_PATTERNS)
    )
    server_port: int = 18080
    server_gguf_path: str = ""
    server_chat_template: str = ""
    server_parallel: int = 1
    server_compute_mode: str = "gpu"
    auto_start_server: bool = False
    cache_clear_after_translation: bool = True
    model_profiles: dict[str, dict] = field(default_factory=dict)
    cloud_models: list[str] = field(
        default_factory=lambda: [m["name"] for m in CLOUD_MODELS_CONFIG]
    )
    last_local_base_url: str = "http://127.0.0.1:17580/v1"
    last_local_api_key: str = "ollama"
    last_local_model: str = "local"
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

    When the file exists but has problems, a backup copy is kept before the
    values are repaired in memory, so the original file is never lost.
    """
    path = config_dir() / "config.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return AppSettings(), None
    except (OSError, ValueError) as exc:
        backup_config()
        return (
            AppSettings(),
            f"Nie można odczytać konfiguracji: {exc}. "
            "Użyto ustawień domyślnych.",
        )

    settings, problems = AppSettings.from_dict(data)
    if problems:
        backup_config()
        return settings, (
            "Wykryto problemy w konfiguracji: " + "; ".join(problems)
            + " Użyto wartości domyślnych dla błędnych pól."
        )
    return settings, None


def backup_config() -> Optional[Path]:
    """Copy the current config.json to a timestamped backup file.

    Returns the backup path, or ``None`` when there is nothing to back up.
    """
    path = config_dir() / "config.json"
    if not path.is_file():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"config.backup-{stamp}.json")
    try:
        shutil.copy2(path, backup)
        return backup
    except OSError:
        return None


def reset_settings() -> tuple[AppSettings, Optional[Path]]:
    """Restore default settings, preserving non-configuration fields.

    The current file is first backed up (timestamped), then defaults are
    written. Paths used by the user (``last_input``, ``last_output``,
    ``glossary_path``) are kept so the user does not have to re-pick them.
    """
    backup = backup_config()
    current = load_settings()[0]
    defaults = AppSettings()
    defaults.last_input = current.last_input
    defaults.last_output = current.last_output
    defaults.glossary_path = current.glossary_path
    save_settings(defaults)
    return defaults, backup


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
    if name in _DICT_FIELDS:
        return isinstance(value, dict) and all(
            isinstance(k, str) and isinstance(v, dict)
            for k, v in value.items()
        )
    return isinstance(value, str)