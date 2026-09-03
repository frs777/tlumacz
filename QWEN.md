# QWEN.md — Tłumacz

Narzędzie do tłumaczenia dokumentów oparte na AI z interfejsem graficznym Qt (PySide6). Tłumaczy pliki Markdown/tekstowe/DOCX/ODT/EPUB/PDF na polski (lub inny język) przy użyciu dowolnego API zgodnego z OpenAI — testowane z lokalnym serwerem Ollama/llama.cpp.

**Wersja:** 0.19.1  
**Status:** wersja robocza/testowa  
**Licencja:** MIT

---

## Technologie

- **Python 3.10+**
- **PySide6** (Qt 6) — interfejs graficzny
- **openai** SDK — komunikacja z API tłumaczenia
- **PyMuPDF** — ekstrakcja i zapis tekstu w PDF z zachowaniem pozycji
- **llama-server** — opcjonalnie zarządzany lokalny serwer z modelem GGUF
- **SQLite** — cache tłumaczeń (`~/.config/tlumacz/cache.db`)
- **pytest** — testy

---

## Struktura projektu

```
tlumacz/
├── core.py                # Logika tłumaczenia (bez zależności Qt)
├── cache.py               # Cache tłumaczeń SQLite (auto-cleanup >7 dni)
├── server.py              # Zarządzany proces llama-server
├── extract.py             # Ekstrakcja tekstu z dokumentów
├── preprocess.py          # Preprocessing tekstu (protect/restore)
├── glossary.py            # Obsługa słowników (CSV)
├── skill.py               # System skills (Markdown, HTML, DOCX, ODT)
├── convert.py             # Konwersja formatów
└── qt_gui/
    ├── app.py             # Punkt wejścia (main())
    ├── config.py          # Trwałe ustawienia (~/.config/tlumacz/config.json)
    ├── main_window.py     # Główne okno Qt Widgets
    ├── worker.py          # QThread workers (tłumaczenie, restart serwera)
    ├── theme.py           # Motywy QSS
    └── resources/         # Motyw QSS + ikona SVG

tests/
├── conftest.py            # Fixture'y pytest (offscreen, config_home)
├── test_cache.py          # Testy cache (9 testów)
├── test_core.py           # Testy logiki tłumaczenia
├── test_main_window.py    # Testy GUI (offscreen)
└── ...                    # Inne testy jednostkowe
```

---

## Komendy

### Uruchomienie aplikacji

```bash
# Zainstaluj w trybie deweloperskim
pip install -e .

# Uruchom GUI
tlumacz

# Lub bezpośrednio
python -m tlumacz.qt_gui.app

# Headless (bez wyświetlacza)
QT_QPA_PLATFORM=offscreen python -m tlumacz.qt_gui.app
```

### Testy

```bash
# Wszystkie testy
pytest tests/

# Z timeoutem
pytest tests/ --timeout=60

# Tylko testy cache
pytest tests/test_cache.py -v

# Tylko testy GUI (offscreen)
pytest tests/test_main_window.py -v
```

### Build i pakowanie

```bash
# Build wheel
python -m build --wheel

# Arch Linux (AUR)
makepkg -si
```

---

## Architektura

### Tłumaczenie w tle

- **TranslateWorker** (QObject) + **QThread** — tłumaczenie nie blokuje GUI
- **multiprocessing.Process** — izolacja procesu tłumaczenia (bezpieczny cancel)
- **Kooperatywny cancel** — `cancel_event` (multiprocessing.Event) + eskalacja terminate/kill
- **ServerRestartWorker** — restart serwera poza wątkiem GUI

### Cache tłumaczeń

- **SQLite** w `~/.config/tlumacz/cache.db`
- Klucz: hash(chunk + system_prompt + skill + model + temperature)
- **Auto-cleanup**: wpisy starsze niż 7 dni usuwane przy starcie
- **Statystyki**: hits/misses wyświetlane w logach po każdym tłumaczeniu
- Domyślnie włączony (`cache_enabled=True` w `TranslatorConfig`)

### Formaty dokumentów

- **Markdown/TXT** — bezpośrednie tłumaczenie
- **DOCX/ODT** — round-trip z zachowaniem struktury XML
- **EPUB** — round-trip z zachowaniem struktury archiwum
- **HTML** — tłumaczenie z ochroną tagów
- **PDF** — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR)

### System skills

Skills to pliki `.md` w `tlumacz/skills/` lub `~/.config/tlumacz/skills/` z instrukcjami dla konkretnych formatów (Markdown, HTML, DOCX, ODT). Aktywowane automatycznie na podstawie rozszerzenia pliku.

---

## Konfiguracja

Ustawienia w `~/.config/tlumacz/config.json`:

```json
{
  "base_url": "http://127.0.0.1:8080/v1",
  "api_key": "ollama",
  "model": "qwen2.5-coder-7b-instruct-q5_k_m",
  "chunk_size": 4000,
  "temperature": 0.1,
  "target_language": "Polish",
  "cache_enabled": true,
  "auto_start_server": false,
  "server_port": 18080,
  "server_gguf_path": "/ścieżka/do/model.gguf"
}
```

---

## Konwencje deweloperskie

### Język

- **Dokumentacja**: polski
- **Kod**: angielski (komentarze, nazwy zmiennych)
- **Logi**: polski (komunikaty dla użytkownika)

### Qt/PySide6

- **QThread + QObject.moveToThread** — operacje w tle
- **Sygnały/sloty** — komunikacja między wątkami
- **Nie blokuj wątku GUI** — operacje sieciowe/subproces w workerach
- **QThread.terminate()** — ostateczność (tylko przy zamknięciu aplikacji)

### Testy

- **pytest** z fixture'ami (`conftest.py`)
- **Offscreen** — `QT_QPA_PLATFORM=offscreen` dla testów GUI
- **config_home** — tymczasowy katalog konfiguracyjny dla testów
- **Fake clients** — mockowane klienta OpenAI w testach
- **cache_enabled=False** — wyłączone cache w testach jednostkowych

### Cache

- **Thread-safe** — `threading.Lock` dla operacji SQLite
- **Auto-cleanup** — stare wpisy usuwane przy inicjalizacji
- **Statystyki** — hits/misses resetowane po każdym tłumaczeniu

---

## Znane ograniczenia

- **Jakość tłumaczenia** zależy od modelu
- **Skill ODT niekompatybilny z kodem** — opisuje "Markdown" ale kod tłumaczy XML in-place → wyciek promptów. ODT bez skilla działa poprawnie. Do naprawy.
- **Wielojęzyczne dokumenty** — mogą wymagać wzmocnienia promptów
- **HTML** — tłumaczenie z ochroną tagów wymaga dalszych testów

---

## Dokumentacja

- `README.md` — instrukcja użytkownika (polski)
- `README.en.md` — instrukcja użytkownika (angielski)
- `PODSUMOWANIE.md` — szczegółowy stan projektu
- `do_zrobienia.md` — lista zadań
- `DEBUG_QT.md` — analiza problemów Qt/threading
- `wydajnosc.md` — analiza wydajności i opcje optymalizacji
- `CHANGELOG.md` — historia zmian

---

## Przydatne pliki

- `~/.config/tlumacz/config.json` — konfiguracja użytkownika
- `~/.config/tlumacz/cache.db` — cache tłumaczeń
- `~/.config/tlumacz/debug.log` — logi diagnostyczne (slow chunks)
- `~/.config/tlumacz/skills/` — skills użytkownika

---

## Licencja

MIT — zobacz `LICENSE.txt`
