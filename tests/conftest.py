import os

import pytest


@pytest.fixture(autouse=True)
def offscreen_platform():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    return tmp_path / "config"
