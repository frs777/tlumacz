"""Tests for config.json loading, validation and persistence."""

import json

from tlumacz.qt_gui.config import (
    AppSettings,
    backup_config,
    load_settings,
    reset_settings,
    save_settings,
)


def test_clean_roundtrip(config_home):
    settings = AppSettings(base_url="http://x/v1", temperature=0.5)
    save_settings(settings)
    loaded, warning = load_settings()
    assert warning is None
    assert loaded.base_url == "http://x/v1"
    assert loaded.temperature == 0.5


def test_missing_file_is_normal_first_run(config_home):
    settings, warning = load_settings()
    assert warning is None
    assert settings.base_url == AppSettings().base_url


def test_corrupted_json_warns(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json!!", encoding="utf-8")
    settings, warning = load_settings()
    assert warning is not None
    assert settings.base_url == AppSettings().base_url


def test_non_object_json_warns(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[1, 2, 3]", encoding="utf-8")
    settings, warning = load_settings()
    assert warning is not None
    assert settings.base_url == AppSettings().base_url


def test_unknown_fields_and_bad_types(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "base_url": "http://z/v1",
                "bogus": 1,
                "chunk_size": "abc",
                "auto_start_server": 1,
                "temperature": "x",
            }
        ),
        encoding="utf-8",
    )
    settings, warning = load_settings()
    assert settings.base_url == "http://z/v1"
    assert settings.chunk_size == AppSettings().chunk_size
    assert settings.auto_start_server is False
    assert settings.temperature == AppSettings().temperature
    for fragment in ("bogus", "chunk_size", "auto_start_server", "temperature"):
        assert fragment in warning


def test_enabled_skills_list_roundtrip(config_home):
    save_settings(AppSettings(enabled_skills=["Markdown", "HTML"]))
    loaded, warning = load_settings()
    assert warning is None
    assert loaded.enabled_skills == ["Markdown", "HTML"]


def test_enabled_skills_wrong_type_warns(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"enabled_skills": "notalist"}), encoding="utf-8")
    settings, warning = load_settings()
    assert "enabled_skills" in warning
    assert settings.enabled_skills == []


def test_backup_config_creates_timestamped_copy(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"base_url": "http://old/v1"}', encoding="utf-8")

    backup = backup_config()

    assert backup is not None
    assert backup.name.startswith("config.backup-")
    assert backup.read_text(encoding="utf-8") == '{"base_url": "http://old/v1"}'
    assert path.read_text(encoding="utf-8") == '{"base_url": "http://old/v1"}'


def test_backup_config_no_file_returns_none(config_home):
    assert backup_config() is None


def test_reset_settings_restores_defaults_keeps_user_paths(config_home):
    save_settings(
        AppSettings(
            base_url="http://custom/v1",
            chunk_size=9999,
            temperature=0.9,
            model="custom-model",
            last_input="/tmp/in.md",
            last_output="/tmp/out_pl.md",
            glossary_path="/home/u/glos.csv",
        )
    )

    defaults, backup = reset_settings()

    assert backup is not None and backup.name.startswith("config.backup-")
    assert defaults.base_url == AppSettings().base_url
    assert defaults.chunk_size == AppSettings().chunk_size
    assert defaults.model == AppSettings().model
    assert defaults.last_input == "/tmp/in.md"
    assert defaults.last_output == "/tmp/out_pl.md"
    assert defaults.glossary_path == "/home/u/glos.csv"

    reloaded, warning = load_settings()
    assert warning is None
    assert reloaded.base_url == AppSettings().base_url
    assert reloaded.last_input == "/tmp/in.md"


def test_corrupted_json_is_backed_up(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json!!", encoding="utf-8")

    load_settings()

    backups = sorted((config_home / "tlumacz").glob("config.backup-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{not json!!"


def test_model_profiles_roundtrip(config_home):
    save_settings(
        AppSettings(
            model_profiles={
                "/home/u/m.gguf": {"chat_template": "chatml"},
                "/home/u/g.gguf": {},
            }
        )
    )
    loaded, warning = load_settings()
    assert warning is None
    assert loaded.model_profiles["/home/u/m.gguf"]["chat_template"] == "chatml"


def test_model_profiles_wrong_type_warns(config_home):
    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model_profiles": "nope"}), encoding="utf-8")
    settings, warning = load_settings()
    assert "model_profiles" in warning
    assert settings.model_profiles == {}
