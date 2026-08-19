"""Tests for config.json loading, validation and persistence."""

import json

from tlumacz.qt_gui.config import AppSettings, load_settings, save_settings


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
