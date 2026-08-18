# Translator Agent

An AI-powered document translation tool with a **Qt GUI (PySide6)**. It translates
Markdown/text files into Polish (or another supported language) using any
OpenAI-compatible API — tested against a local Ollama/llama.cpp server.

## Version

Current version: **0.5.0**

## Features

- 🖥️ **Qt GUI** built with PySide6 / Qt Widgets
- 📄 **File selection** for input and output paths
- ⚙️ **Configurable API**: base URL, API key, model, chunk size, temperature, target language
- 🔄 **Background translation** on a worker thread — the UI never freezes
- ⏹️ **Cancel** running translation at any time
- 📊 **Progress bar** and live log view
- 👁️ **Preview** of the translated output
- 💾 **Persistent settings** in `~/.config/agent-translator/config.json`
- 🎨 **Dark QSS theme** with bundled SVG icon

## Requirements

- Python 3.10+
- `PySide6`, `openai` (installed automatically via pip/AUR)

## Installation

### From source (development)

```bash
pip install -e .
agent-translator
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
After install, launch the app globally with `agent-translator` or from your
application menu.

## Usage

1. Run `agent-translator`
2. Choose the **input file** to translate
3. Choose the **output file** (defaults to `name_pl.ext`)
4. Adjust **API settings** if needed (default: `http://127.0.0.1:8080/v1`, model `qwen2.5-coder-7b-instruct-q5_k_m`)
5. Click **Tłumacz** (Translate)
6. Monitor progress in the log, then review the **preview** panel

## API compatibility

The app speaks the OpenAI Chat Completions protocol, so it works with:

- Local Ollama / llama.cpp servers (`http://127.0.0.1:8080/v1`)
- Cloud OpenAI-compatible endpoints

## Development

```bash
# Run tests / sanity checks
python -c "from agent_translator.qt_gui.app import main; print('OK')"

# Run the GUI without a display (headless check)
QT_QPA_PLATFORM=offscreen python -m agent_translator.qt_gui.app
```

## Project structure

```
agent_translator/
├── core.py                # Reusable translation logic (no Qt deps)
└── qt_gui/
    ├── app.py             # Entry point (main())
    ├── config.py          # Per-user settings persistence
    ├── main_window.py     # Qt Widgets main window
    ├── worker.py          # QThread worker for background translation
    └── resources/         # QSS theme + SVG icon
```

## License

MIT