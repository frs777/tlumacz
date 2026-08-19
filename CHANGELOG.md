# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.14.0] - 2026-08-19

### Added
- "Odśwież" button in the skills group: re-discovers skills from the user
  directory without restarting the app
- "Importuj skilla..." button: pick any `.md` file (from hidden folders
  too), validate its `name`/`formats` frontmatter and copy it into
  `~/.config/tlumacz/skills/`

### Changed
- All file dialogs (input, output, GGUF, glossary, skill import) now show
  hidden files and folders, so paths like `~/.config` and dot-directories
  are reachable

## [0.13.0] - 2026-08-19

### Added
- User skills: `*.md` files placed in `<config_dir>/skills/`
  (e.g. `~/.config/tlumacz/skills/`) are discovered alongside the bundled
  ones; a user skill with the same `name` overrides the bundled one
- `save_skill()` helper to write a user skill file with `name`/`formats`
  frontmatter into the user skills directory

### Changed
- Help tab documents how to add user skills
- `discover_skills()` now merges bundled + user skills (user wins by name)

## [0.12.0] - 2026-08-19

### Changed
- Main window split into tabs to reduce clutter on the translation screen:
  - **Tłumaczenie** — input/output files, translate/cancel, progress, log, preview
  - **Ustawienia** — API settings, local server, glossary, skills
  - **Pomoc** — built-in help (Polish/English) covering LLM setup, local
    server, glossary, skills, theme and `config.json` fields

### Added
- Help tab with a language selector (PL/EN) rendering short usage docs

## [0.11.0] - 2026-08-19

### Added
- Skill injection for format-specific translation instructions:
  - Bundled skills as `.md` files in the `tlumacz/skills/` package with
    `name`/`formats` frontmatter (`markdown`, `plaintext`, `html`)
  - "Skille" group in the GUI with a checkbox per skill; enabled skills are
    persisted in `config.json` as `enabled_skills`
  - When the input file's extension matches an enabled skill, its
    instructions are appended to the translation system prompt
- Config field: `enabled_skills` (list of skill names, validated)

### Testing
- Added `tests/` suite (33 tests) covering glossary parsing, config
  validation, skill discovery/matching, the core translation engine
  (chunking, prompts, cancellation) and offscreen GUI smoke tests; run with
  `python3 -m pytest tests/`

## [0.10.0] - 2026-08-19

### Added
- "Serwer lokalny" group in the GUI: server port, GGUF model file path (with file picker) and an "auto-start server with the app" checkbox — previously only editable via `config.json`
- Custom translation prompt: an optional "Własny prompt" field (styl, terminologia, ton) that replaces the default system prompt; the glossary is still appended independently
- Config field: `system_prompt`

### Changed
- `_collect_settings` reads the server settings from the GUI fields instead of copying them from the previously loaded config

## [0.9.0] - 2026-08-19

### Added
- Config validation: `config.json` is checked on load for unknown fields and wrong-typed values; affected fields fall back to defaults and the GUI shows a warning dialog instead of silently ignoring the problem

### Changed
- `load_settings()` now returns `(settings, warning)`; `app.py` prints the warning to stderr, `main_window.py` surfaces it in a dialog

## [0.8.0] - 2026-08-19

### Changed
- The default translation system prompt now instructs the model to return the text unchanged when it is already in the target language, so already-Polish (or otherwise already-translated) input is not translated a second time

## [0.7.0] - 2026-08-19

### Added
- Glossary support: a two-column CSV glossary (`source,target`) injected into the translation system prompt so the model uses fixed translations
- New `tlumacz/glossary.py` module (`Glossary`) free of Qt dependencies: CSV parsing with header detection, `#`-prefix stripping (inflection-dictionary format), case-insensitive deduplication, identity-pair filtering and a configurable entry cap
- New "Glosariusz" group in the GUI: file picker, live entry count, and manual entry addition (`termin` + `tłumaczenie`) that appends to the selected CSV
- Config field: `glossary_path`
- Only the first 300 (non-identity) glossary entries are injected per prompt, and CSV reading stops early at that cap so huge dictionaries load instantly
- Translation log reports when a glossary is in use

## [0.6.0] - 2026-08-19

### Added
- Theme switching in the GUI: `system` (follows the OS color scheme), `light` and `dark`, selectable via a new "Motyw" combo box in the API settings group
- New `tlumacz/qt_gui/theme.py` module (`resolve_theme`, `apply_theme`, `load_stylesheet`)
- Separate QSS stylesheets: `style_dark.qss` (Catppuccin Mocha) and `style_light.qss` (Catppuccin Latte)
- The theme re-applies automatically when the OS color scheme changes while in `system` mode
- Config field: `theme` (default `"system"`), persisted immediately on change

### Changed
- `tlumacz/qt_gui/app.py` now applies the theme from `settings.theme` instead of a single hard-coded stylesheet

## [0.5.1] - 2026-08-19

### Added
- Managed local `llama-server` process: the GUI can start its own server in the background on a dedicated port and stop it when the app exits
- New `tlumacz/server.py` module (`LlamaServer`, `ServerConfig`) free of Qt dependencies
- Config fields: `server_port` (default 18080), `server_gguf_path`, `auto_start_server`
- Signal handlers (SIGTERM/SIGINT) plus `atexit` cleanup so the managed server is stopped even on termination

### Fixed
- `_collect_settings` in the main window no longer drops the server config fields when saving settings on window close
- Output path now defaults to the current input file with a language suffix (`name_pl.ext`, `name_en.ext`, ...) every time a new input file is chosen, instead of keeping the path from the last translation
- Language change updates the default output path suffix accordingly

## [0.5.0] - 2026-08-18

### Added
- Qt GUI (PySide6 / Qt Widgets) for translating files to Polish via an OpenAI-compatible API
- Main window with input/output file selection and API settings (base URL, key, model, chunk size, temperature, target language)
- Background translation on a QThread worker (non-blocking UI) with cancel support
- Progress bar, live log view, and translated-output preview
- Persistent per-user settings in `~/.config/tlumacz/config.json`
- QSS dark theme and bundled SVG icon (package resources)
- Python package structure (`tlumacz/`) with `pyproject.toml`, entry point `tlumacz`, `requirements.txt`, `PKGBUILD` (AUR-ready) and `.desktop` file

### Changed
- Extracted translation logic from standalone Python scripts into reusable `tlumacz/core.py`
- Configuration is now data-driven (`TranslatorConfig`) instead of hard-coded in scripts
- Chunk splitting respects line boundaries instead of arbitrary character slices

### Technical Details
- Worker follows the safe `QObject` + `moveToThread` pattern with explicit `quit()`/`wait()` lifecycle
- Core module is free of Qt/CLI dependencies so it can be reused by GUI, CLI, or tests
- `importlib.resources` loads the bundled QSS so styling works after global installation

## [0.4.0] - 2025-06-20

### Added
- Tool call status display in the status line below input box
- Tool call results shown in message history with proper labeling
- Real-time status updates during tool execution
- Visual indicators for tool messages (🔧 icon and magenta color)
- Enhanced message types to support tool call information

### Changed
- Status line now shows tool-specific status (e.g. "Reading file: ...", "Fetching URL: ...")
- Message history displays tool results as separate messages
- Improved visual feedback during AI tool execution

### Technical Details
- Extended Message interface with tool-specific properties
- Added ToolCallbacks interface for status event handling
- Enhanced StatusLine component with tool status support
- Updated MessageHistory component for tool message rendering
- Modified AI client to emit tool call events and status updates

## [0.1.0] - 2025-06-20

### Added
- Initial release of Translator Agent CLI
- Basic chat interface with message history
- Interactive terminal UI using React + Ink
- Welcome message display
- Message input with timestamp
- Status line for feedback
- Exit commands support ('exit' or 'quit')
- TypeScript support with ESM modules
- Build and development scripts

### Technical Details
- Built with TypeScript, React, and Ink v4
- Supports Node.js v20+
- Uses ESM modules for modern JavaScript
- Includes proper error handling for non-TTY environments