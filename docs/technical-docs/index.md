# Tłumacz — Dokumentacja Techniczna

**Wersja:** 0.21.0-dev  
**Data ostatniej aktualizacji:** 2026-09-05  
**Status:** Wersja robocza/testowa

---

## Spis treści

### Dokumentacja użytkownika

- [Podręcznik użytkownika](user-guide.md) — kompletny przewodnik po instalacji, konfiguracji i używaniu aplikacji
- [Treść pomocy GUI](help-content.md) — treść wbudowanej pomocy w zakładce „Pomoc"

### Dokumentacja techniczna

- [Zarządzanie serwerem](server-management.md) — architektura ServerManager, przycisk restart, obsługa llama.cpp
- [Tłumaczenie w chmurze](cloud-translation.md) — konfiguracja modeli chmurowych (Gemini, OpenAI)
- [Modele tłumaczenia](models.md) — rekomendowane modele, TranslateGemma, porównanie jakości

### Dokumentacja developerska

- [Architektura aplikacji](#architektura) — overview komponentów
- [Struktura projektu](#struktura-projektu) — opis plików i katalogów
- [Konfiguracja](#konfiguracja) — plik config.json i jego pola

---

## Szybki start

```bash
# Instalacja w trybie deweloperskim
pip install -e .

# Uruchomienie GUI
tlumacz
```

### Pierwsze tłumaczenie

1. Uruchom aplikację: `tlumacz`
2. Wybierz plik wejściowy (Markdown, TXT, HTML, PDF, DOCX, ODT, EPUB)
3. Wybierz plik wyjściowy (domyślnie `nazwa_pl.rozszerzenie`)
4. Skonfiguruj API w zakładce „API i serwer":
   - **Lokalny serwer**: wskaż plik GGUF, port, zaznacz „Uruchamiaj serwer razem z programem"
   - **Chmura**: wybierz model chmurowy (np. `gemini-3.5-flash`), wprowadź klucz API
5. Kliknij **„Tłumacz"** i obserwuj postęp

---

## Architektura

```
┌─────────────────────────────────────────────────────────┐
│  MainWindow (GUI)                                        │
│  - Zakładki: Tłumaczenie, API i serwer, Dodatki, Pomoc  │
│  - Oddelegowuje operacje serwera do ServerManager        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ServerManager (centralny zarządca serwera)              │
│  - Stan maszyny: IDLE/STARTING/RUNNING/STOPPING         │
│  - Kolejka operacji (zapobiega race conditions)         │
│  - Automatyczny restart przy błędach                     │
│  - Zarządzanie procesem i portem                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  LlamaServer (zarządzanie procesem llama-server)         │
│  - Start/stop procesu llama-server                       │
│  - Health check (is_running)                             │
│  - Obsługa osieroconych procesów (_kill_by_port)         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Translator (logika tłumaczenia)                         │
│  - Chunking tekstu z ochroną sekcji                      │
│  - Równoległe tłumaczenie (ThreadPoolExecutor)           │
│  - Cache tłumaczeń (SQLite)                              │
│  - Round-trip dla DOCX/ODT/EPUB/PDF                      │
└─────────────────────────────────────────────────────────┘
```

### Kluczowe komponenty

| Komponent | Plik | Opis |
|-----------|------|------|
| **MainWindow** | `qt_gui/main_window.py` | Główne okno Qt Widgets, zakładki, przycisk restart |
| **ServerManager** | `qt_gui/worker.py` | Centralny zarządca serwera, maszyna stanów |
| **LlamaServer** | `server.py` | Zarządzanie procesem llama-server, health check |
| **Translator** | `core.py` | Logika tłumaczenia, chunking, cache, round-trip |
| **TranslationCache** | `cache.py` | SQLite cache tłumaczeń, auto-cleanup |
| **AppSettings** | `qt_gui/config.py` | Trwałe ustawienia w `~/.config/tlumacz/config.json` |

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
├── pdf_extractor.py       # Ekstrakcja tekstu z PDF (PyMuPDF)
├── i18n.py                # System lokalizacji (PL/EN)
└── qt_gui/
    ├── app.py             # Punkt wejścia (main())
    ├── config.py          # Trwałe ustawienia (~/.config/tlumacz/config.json)
    ├── main_window.py     # Główne okno Qt Widgets
    ├── worker.py          # QThread workers (tłumaczenie, ServerManager)
    ├── theme.py           # Motywy QSS
    └── resources/         # Motyw QSS + ikona SVG

tests/
├── conftest.py            # Fixture'y pytest (offscreen, config_home)
├── test_cache.py          # Testy cache (9 testów)
├── test_core.py           # Testy logiki tłumaczenia
├── test_main_window.py    # Testy GUI (offscreen)
└── ...                    # Inne testy jednostkowe

docs/
├── technical-docs/        # Dokumentacja techniczna (ten katalog)
│   ├── index.md           # Ten plik
│   ├── user-guide.md      # Podręcznik użytkownika
│   ├── server-management.md
│   ├── cloud-translation.md
│   ├── models.md
│   └── help-content.md
├── STATUS.md              # Aktualny stan projektu
├── TODO.md                # Lista zadań
├── ADR-001-server-manager-architecture.md
└── ...
```

---

## Konfiguracja

Ustawienia w `~/.config/tlumacz/config.json`:

```json
{
  "base_url": "http://127.0.0.1:8080/v1",
  "api_key": "ollama",
  "model": "LOCAL",
  "chunk_size": 4000,
  "temperature": 0.1,
  "target_language": "wykryj do pl",
  "theme": "system",
  "glossary_path": "",
  "system_prompt": "",
  "enabled_skills": [],
  "skip_line_patterns": [],
  "server_port": 18080,
  "server_gguf_path": "/ścieżka/do/model.gguf",
  "server_chat_template": "",
  "server_parallel": 1,
  "server_compute_mode": "gpu",
  "auto_start_server": false,
  "cache_clear_after_translation": true,
  "model_profiles": {},
  "cloud_models": ["gemini-3.5-flash", "gemini-3.5-flash-lite"],
  "last_local_base_url": "http://127.0.0.1:18080/v1",
  "last_local_api_key": "ollama",
  "last_local_model": "local",
  "last_input": "",
  "last_output": ""
}
```

### Kluczowe pola

| Pole | Typ | Opis |
|------|-----|------|
| `base_url` | string | Adres serwera API zgodnego z OpenAI |
| `api_key` | string | Token uwierzytelniający (lokalne serwery ignorują) |
| `model` | string | Nazwa modelu (`LOCAL`, `gemini-3.5-flash`, lub własna) |
| `chunk_size` | int | Rozmiar fragmentu tekstu w znakach (4000-6000) |
| `temperature` | float | Losowość odpowiedzi (0.1-0.3) |
| `target_language` | string | Język docelowy w formacie „wykryj do X" |
| `server_gguf_path` | string | Ścieżka do pliku GGUF dla lokalnego serwera |
| `auto_start_server` | bool | Automatyczne uruchamianie serwera przy starcie |
| `cache_clear_after_translation` | bool | Czyszczenie cache po każdym tłumaczeniu |

---

## Licencja

MIT — zobacz [LICENSE.txt](../../LICENSE.txt)

## Autor

frs — https://github.com/frs777/tlumacz
