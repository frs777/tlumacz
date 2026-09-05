# Tłumacz

> [Polski (PL)](README_pl.md) · [English (EN)](README.en.md)

**AI-powered document translation tool with a Qt (PySide6) graphical interface**

Translate Markdown, TXT, HTML, PDF, DOCX, ODT and EPUB files to Polish (or other languages) using any OpenAI-compatible API — local llama.cpp/Ollama server or cloud Gemini models.

> [!WARNING]
> **⚠️ Early development version — not ready for production use.**
>
> Tłumacz is in active development (v0.21.0-dev). The application may contain bugs,
> and translation quality depends on the LLM model used. **We do not recommend using it in
> production environments or for translating critical documents.**
>
> Currently, the best results are achieved with **TranslateGemma-4b** (~87% quality). Weaker
> models (below 7B parameters) may produce incomplete translations, hallucinations and
> artifacts — especially in binary formats (DOCX, ODT, EPUB, PDF).
>
> If you want to test the application, please report bugs via [Issues](https://github.com/frs777/tlumacz/issues).

> **Version:** 0.21.2 | **Status:** Stable test release | **License:** MIT

---

## 📦 Downloads — binary packages

| System | Format | Download |
|--------|--------|----------|
| **Arch Linux** | `.pkg.tar.zst` | [tlumacz-0.21.2-1-any.pkg.tar.zst](https://github.com/frs777/tlumacz/releases/download/v0.21.2/tlumacz-0.21.2-1-any.pkg.tar.zst) |
| **Debian/Ubuntu** | `.deb` | [tlumacz_0.21.2-1_all.deb](https://github.com/frs777/tlumacz/releases/download/v0.21.2/tlumacz_0.21.2-1_all.deb) |
| **Fedora/RHEL** | `.rpm` | [tlumacz-0.21.2-1.noarch.rpm](https://github.com/frs777/tlumacz/releases/download/v0.21.2/tlumacz-0.21.2-1.noarch.rpm) |
| **Any Linux** | `.AppImage` | [tlumacz-0.21.2-x86_64.AppImage](https://github.com/frs777/tlumacz/releases/download/v0.21.2/tlumacz-0.21.2-x86_64.AppImage) |

> **All packages:** [Releases → v0.21.2](https://github.com/frs777/tlumacz/releases/tag/v0.21.2)

### Installation from packages

```bash
# Arch Linux (from local repo or package)
sudo pacman -U tlumacz-0.21.2-1-any.pkg.tar.zst

# Debian/Ubuntu
sudo dpkg -i tlumacz_0.21.2-1_all.deb

# Fedora/RHEL
sudo dnf install tlumacz-0.21.2-1.noarch.rpm

# AppImage (no installation needed)
chmod +x tlumacz-0.21.2-x86_64.AppImage
./tlumacz-0.21.2-x86_64.AppImage
```

---

## ✨ Features

### 🖥️ Graphical Interface
- **Modern GUI** built on PySide6 / Qt Widgets
- **Dark theme** with included SVG icon
- **Tabs:** Translation, API & Server, Extras, Help
- **Themes:** system, light, dark
- **PL/EN Help** built into the application

### 📄 Supported Formats
| Format | Extension | Format Preservation |
|--------|-----------|-------------------|
| Markdown | `.md`, `.markdown` | ✅ Preserved |
| Text | `.txt` | ✅ Preserved |
| HTML | `.html`, `.htm` | ✅ Preserved (tag protection) |
| PDF | `.pdf` | ⚠️ Text with layout preservation |
| DOCX | `.docx` | ✅ XML round-trip |
| ODT | `.odt` | ✅ XML round-trip |
| EPUB | `.epub` | ✅ XHTML round-trip |

### 🤖 Server Management
- **ServerManager** — central manager with state machine (IDLE/STARTING/RUNNING/STOPPING)
- **Smart server button** — 4 states: restart/stop/start/info
- **Managed llama-server** — automatic start and stop
- **Orphaned process handling** — automatic cleanup
- **Chat templates** — jinja, chatml, translategemma

### ☁️ Cloud Translation
- **Google Gemini** — gemini-3.5-flash, gemini-3.5-flash-lite
- **OpenAI** — GPT-4, GPT-3.5
- **Other APIs** — any OpenAI Chat Completions compatible
- **Switching** — quick switching between cloud and local server
- **Settings memory** — remembers last local settings

### 🌍 Translation
- **"Detect to X" format** — automatic source language detection
- **10 target languages** — Polish, English, German, French, Spanish, Italian, Ukrainian, Czech, Dutch, Russian
- **Parallel translation** — ThreadPoolExecutor for multiple chunks
- **Translation cache** — SQLite with auto-cleanup (>7 days)
- **Fragment protection** — code, URLs, variables are protected from translation

### 📚 Extras
- **CSV Glossary** — force fixed translations for selected terms
- **Skills system** — instructions for specific formats (Markdown, HTML, DOCX, ODT, EPUB)
- **Auto-select skill** — automatic skill selection matching the file
- **Custom skills** — add your own instructions in `~/.config/tlumacz/skills/`

### 🔄 Background Translation
- **QThread + QObject** — translation doesn't block the GUI
- **multiprocessing.Process** — translation process isolation
- **Cooperative cancel** — safe cancellation at any time
- **Progress bar** — real-time translation progress
- **Timer** — translation duration
- **Live log** — status messages

---

## 🚀 Quick Start

### Installation

```bash
# From source (development)
pip install -e .

# Run
tlumacz
```

### Arch Linux

```bash
# From local repository
sudo pacman -S tlumacz

# Or build from PKGBUILD
makepkg -si
```

### First Translation (Local Server)

1. **Run the application:** `tlumacz`
2. **Go to "API & Server" tab**
3. **Specify GGUF file** in "Model file (GGUF)" field
4. **Check** "Run server with program"
5. **Click** "Start server"
6. **Return to "Translation" tab**
7. **Select** input and output files
8. **Click** "Translate"

### First Translation (Cloud)

1. **Run the application:** `tlumacz`
2. **Go to "API & Server" tab**
3. **Select model** from combo box (e.g., `gemini-3.5-flash`)
4. **Enter API key** in "API key" field
5. **Return to "Translation" tab** and start

---

## 📖 Documentation

### User Guide

- [**User Guide**](docs/technical-docs/user-guide.md) — complete guide to installation, configuration and usage
- [GUI Help Content](docs/technical-docs/help-content.md) — built-in help content

### Technical Documentation

- [**Server Management**](docs/technical-docs/server-management.md) — ServerManager architecture, restart button, llama.cpp
- [**Cloud Translation**](docs/technical-docs/cloud-translation.md) — Gemini, OpenAI, other API configuration
- [**Translation Models**](docs/technical-docs/models.md) — TranslateGemma, quality comparison, recommendations

### For Developers

- [Documentation Index](docs/technical-docs/index.md) — architecture, project structure, configuration
- [STATUS.md](docs/STATUS.md) — current project status
- [TODO.md](docs/TODO.md) — task list
- [CHANGELOG.md](CHANGELOG.md) — changelog
- [ADR-001](docs/ADR-001-server-manager-architecture.md) — ServerManager architecture

---

## 🏆 Recommended Models

### Best Quality (Local)

**TranslateGemma-4b-it.Q4_K_M** — Google's specialized translation model

- **Quality:** 87%
- **Speed:** ~10 minutes (5000 word document, GPU)
- **Requirements:** 4 GB VRAM
- **Chat template:** `translategemma (language codes)`

[Detailed description →](docs/technical-docs/models.md#translategemma--szczegółowy-opis)

### Best Speed (Cloud)

**gemini-3.5-flash-lite** — fastest cloud model

- **Quality:** ~90%
- **Speed:** ~2 minutes (5000 word document)
- **Requirements:** None (cloud)
- **Cost:** Free (1500 RPM)

### Best Balance

**gemini-3.5-flash** — high quality in the cloud

- **Quality:** ~92%
- **Speed:** ~3 minutes
- **Cost:** Free (60 RPM)

---

## ⚙️ Configuration

### Configuration File

Settings in `~/.config/tlumacz/config.json`:

```json
{
  "base_url": "http://127.0.0.1:18080/v1",
  "api_key": "ollama",
  "model": "LOCAL",
  "chunk_size": 4000,
  "temperature": 0.1,
  "target_language": "wykryj do pl",
  "server_port": 18080,
  "server_gguf_path": "/path/to/model.gguf",
  "server_chat_template": "",
  "auto_start_server": false,
  "cache_clear_after_translation": true
}
```

### Parameters Table

| Parameter | What it does | Recommended value | Why |
|-----------|-------------|-------------------|-----|
| **Base URL** | API server address | `http://127.0.0.1:18080/v1` | Server must speak OpenAI protocol |
| **API key** | `Authorization: Bearer` token | `ollama` (local) | Local servers ignore the key |
| **Model** | Model name | `local` / `gemini-3.5-flash` | Must be available on the server |
| **Block size** | Text chunk (characters) | **4000–6000** | Smaller = better context; larger = fewer calls |
| **Temperature** | Response randomness | **0.1–0.3** | Low = faithful translation |

---

## 🖥️ Local Server

### Managed Server (Recommended)

Tłumacz can automatically manage the `llama-server` process:

1. Specify GGUF file in "API & Server" tab
2. Check "Run server with program"
3. Run the application — server starts automatically
4. Close the application — server is stopped

### Smart Server Button

The button changes label depending on the state:

| Server State | Auto-start | Label | Action |
|--------------|------------|-------|--------|
| ✅ Running | ✅ | **Restart server** | Stop and restart |
| ✅ Running | ❌ | **Stop server** | Stop only |
| ❌ Stopped | ✅ | **Start server** | Start |
| ❌ Stopped | ❌ | **Check the box...** | Show info |

[Detailed description →](docs/technical-docs/server-management.md#przycisk-multifunkcyjny-restart-serwera)

### Manual Launch

```bash
llama-server \
  -m /path/to/model.gguf \
  --host 127.0.0.1 \
  --port 18080 \
  --ctx-size 8192 \
  --jinja
```

---

## ☁️ Cloud Translation

### Google Gemini

1. Select model from combo box (e.g., `gemini-3.5-flash`)
2. Base URL will be set automatically
3. Enter API key from [Google AI Studio](https://aistudio.google.com/)

| Model | RPM Limit | Cost |
|-------|-----------|------|
| gemini-3.5-flash | 60 | Free* |
| gemini-3.5-flash-lite | 1500 | Free* |

### Other APIs

Tłumacz works with any OpenAI-compatible API:
- **OpenAI** — GPT-4, GPT-3.5
- **Groq** — fast open-source models
- **Together AI** — various models
- **Azure OpenAI** — enterprise

[Detailed description →](docs/technical-docs/cloud-translation.md)

---

## 📚 Glossary

Two-column CSV file `source,translation`:

```csv
source,target
API,API
backend,backend
machine learning,machine learning
```

**Advantages:**
- Forces fixed translations for key terms
- Automatic filtering — only terms from source text
- Up to 5000 entries

---

## 🎯 Skills

Skills are model instructions matched to file format:

```markdown
---
name: Markdown
formats: md, markdown
---
Preserve Markdown formatting: headings, lists, code blocks, links.
```

**Built-in skills:** Markdown, HTML, DOCX, ODT, EPUB, PDF, Plaintext

**Custom skills:** Add `.md` files in `~/.config/tlumacz/skills/`

---

## 🧪 Tests

```bash
# All tests
pytest tests/ -v

# GUI tests only (offscreen)
QT_QPA_PLATFORM=offscreen pytest tests/test_main_window.py -v

# Cache tests only
pytest tests/test_cache.py -v
```

**Status:** 102 unit tests — all passing ✅

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  MainWindow (GUI)                                        │
│  - Tabs: Translation, API & Server, Extras, Help        │
│  - ServerManager (central manager)                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ServerManager                                           │
│  - State: IDLE/STARTING/RUNNING/STOPPING                │
│  - Operation queue (no race conditions)                 │
│  - Orphaned process handling                             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  LlamaServer / Cloud API                                 │
│  - llama-server (local)                                  │
│  - Gemini / OpenAI / other (cloud)                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Translator                                              │
│  - Chunking with section protection                      │
│  - Parallel translation (ThreadPoolExecutor)             │
│  - Cache (SQLite)                                        │
│  - Round-trip DOCX/ODT/EPUB/PDF                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Requirements

### Minimum

- **Python 3.10+**
- **Operating system:** Linux (tested on Arch Linux/KDE Plasma), Windows, macOS
- **RAM:** 4 GB (8 GB recommended for 7B+ models)

### Optional

- **llama-server** — for built-in managed server
- **GPU** — recommended for local models (Vulkan/CUDA)
- **pandoc** — for DOCX extraction
- **poppler-utils** — for PDF extraction

### Python Dependencies

```
openai>=1.0
PySide6>=6.5
PyMuPDF>=1.24.0
```

---

## 📂 Project Structure

```
tlumacz/
├── core.py                # Translation logic (no Qt)
├── cache.py               # SQLite translation cache
├── server.py              # Managed llama-server process
├── extract.py             # Text extraction from documents
├── preprocess.py          # Preprocessing (protect/restore)
├── glossary.py            # CSV dictionary handling
├── skill.py               # Skills system
├── pdf_extractor.py       # PDF extraction (PyMuPDF)
├── i18n.py                # PL/EN localization
└── qt_gui/
    ├── app.py             # Entry point
    ├── config.py          # Persistent settings
    ├── main_window.py     # Main Qt window
    ├── worker.py          # QThread workers, ServerManager
    ├── theme.py           # QSS themes
    └── resources/         # QSS theme + SVG icon

docs/
└── technical-docs/        # Technical documentation
    ├── index.md
    ├── user-guide.md
    ├── server-management.md
    ├── cloud-translation.md
    ├── models.md
    └── help-content.md

tests/                     # Unit tests (102 tests)
```

---

## 🔧 Development

```bash
# Clone
git clone https://github.com/frs777/tlumacz.git
cd tlumacz

# Development installation
pip install -e .

# Run
tlumacz

# Tests
pytest tests/ -v

# Headless (no display)
QT_QPA_PLATFORM=offscreen python -m tlumacz.qt_gui.app
```

---

## 🐛 Known Limitations

- **Translation quality** depends on the model used
- **PDF** — text translation without OCR (scans not supported)
- **ODT skill** — incompatible with code (ODT without skill works correctly)
- **Multilingual documents** — may require prompt strengthening

---

## 📋 Roadmap

### In Progress
- [ ] PDF round-trip with layout preservation
- [ ] Pre-release stabilization
- [ ] GUI Help → i18n

### Planned
- [ ] OCR for PDF scans
- [ ] Chat template detection by model probe
- [ ] Full config.json editing via GUI
- [ ] LaTeX, reStructuredText, AsciiDoc support

---

## 🤝 Contributing

Project is developed by [frs](https://github.com/frs777).

Bug reports and feature requests are welcome — open an [Issue](https://github.com/frs777/tlumacz/issues).

---

## 📄 License

MIT — see [LICENSE.txt](LICENSE.txt)

---

## 🔗 Links

- **Repository:** https://github.com/frs777/tlumacz
- **Issues:** https://github.com/frs777/tlumacz/issues
- **Documentation:** [docs/technical-docs/](docs/technical-docs/)

---

<p align="center">
  <strong>Tłumacz</strong> — AI document translation<br>
  <sub>Version 0.21.2 | MIT License | Author: frs</sub>
</p>
