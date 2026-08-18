# Tłumacz

An AI-powered document translation tool with a **Qt GUI (PySide6)**. It translates
Markdown/text files into Polish (or another supported language) using any
OpenAI-compatible API — tested against a local Ollama/llama.cpp server.

> [Polski (PL)](README.md) · English (EN)

## Version

Current version: **0.5.1**

## Features

- 🖥️ **Qt GUI** built with PySide6 / Qt Widgets
- 📄 **File selection** for input and output paths
- ⚙️ **Configurable API**: base URL, API key, model, chunk size, temperature, target language
- 🔄 **Background translation** on a worker thread — the UI never freezes
- ▶️ **Managed local server** — the app can start its own `llama-server` on a
  dedicated port (default 18080) with a user-selected GGUF file and stop it on exit
- ⏹️ **Cancel** running translation at any time
- 📊 **Progress bar** and live log view
- 👁️ **Preview** of the translated output
- 💾 **Persistent settings** in `~/.config/tlumacz/config.json`
- 🎨 **Dark QSS theme** with bundled SVG icon

## Requirements

- Python 3.10+
- `PySide6`, `openai` (installed automatically via pip/AUR)
- Optional: `llama-server` for the built-in managed server

## Installation

### From source (development)

```bash
pip install -e .
tlumacz
```

### Build a wheel

```bash
python -m build --wheel
```

### Arch Linux (AUR)

The repository includes a ready `PKGBUILD`. Package it with:

```bash
makepkg -si
```

Dependencies are resolved from official repos (`pyside6`) and AUR (`python-openai`).
After install, launch the app globally with `tlumacz` or from your
application menu.

## Usage

1. Run `tlumacz`
2. Choose the **input file** to translate
3. Choose the **output file** (defaults to `name_<lang>.ext`, e.g. `name_pl.md`)
4. Adjust **API settings** if needed (default: `http://127.0.0.1:8080/v1`, model `qwen2.5-coder-7b-instruct-q5_k_m`)
5. Click **Tłumacz** (Translate)
6. Monitor progress in the log, then review the **preview** panel

### Managed server

In `~/.config/tlumacz/config.json` set:

```json
{
  "auto_start_server": true,
  "server_port": 18080,
  "server_gguf_path": "/path/to/model.gguf"
}
```

The app then starts `llama-server` in the background on that port, points the
API settings at it, and stops the server when the window is closed.

## API compatibility

The app speaks the OpenAI Chat Completions protocol, so it works with:

- Local Ollama / llama.cpp servers (`http://127.0.0.1:8080/v1`)
- Cloud OpenAI-compatible endpoints

## Development

```bash
# Run tests / sanity checks
python -c "from tlumacz.qt_gui.app import main; print('OK')"

# Run the GUI without a display (headless check)
QT_QPA_PLATFORM=offscreen python -m tlumacz.qt_gui.app
```

## Project structure

```
tlumacz/
├── core.py                # Reusable translation logic (no Qt deps)
├── server.py              # Managed llama-server process (no Qt deps)
└── qt_gui/
    ├── app.py             # Entry point (main())
    ├── config.py          # Per-user settings persistence
    ├── main_window.py     # Qt Widgets main window
    ├── worker.py          # QThread worker for background translation
    └── resources/         # QSS theme + SVG icon
```

## License

MIT