# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows desktop build of Tłumacz."""

from PyInstaller.utils.hooks import collect_data_files


project_root = "../.."

resources = collect_data_files(
    "tlumacz.qt_gui.resources",
    includes=["*.qss", "*.svg"],
)
skills = collect_data_files(
    "tlumacz.skills",
    includes=["*.md"],
)

analysis = Analysis(
    ["../../tlumacz/qt_gui/app.py"],
    pathex=[project_root],
    binaries=[],
    datas=resources + skills,
    hiddenimports=[],
    excludes=[
        # Optional backends are not bundled in the base Windows build.
        # The GUI detects their absence and keeps the other backends usable.
        "fastapi",
        "uvicorn",
        "transformers",
        "torch",
        "accelerate",
        "safetensors",
        "openvino",
        "openvino_genai",
    ],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="Tlumacz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="tlumacz.ico",
)
