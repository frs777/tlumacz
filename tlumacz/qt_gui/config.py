"""Persistent configuration for the Tłumacz GUI.

Settings are stored as JSON in ``~/.config/tlumacz/config.json`` so
the application works when installed globally (AUR) and per-user.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

APP_NAME = "tlumacz"


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
    server_port: int = 18080
    server_gguf_path: str = ""
    auto_start_server: bool = False
    last_input: str = ""
    last_output: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


def load_settings() -> AppSettings:
    """Load settings from disk, falling back to defaults on any error."""
    path = config_dir() / "config.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return AppSettings.from_dict(json.load(f))
    except (OSError, ValueError):
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    """Persist settings to disk, creating the config directory if needed."""
    path = config_dir() / "config.json"
    config_dir().mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=2)
    tmp.replace(path)
