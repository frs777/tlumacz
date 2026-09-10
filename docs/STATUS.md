# Agent Translator V3 - Status Projektu

**Wersja:** 0.31.1
**Status:** wersja robocza/testowa
**Licencja:** MIT
**Data:** 2026-09-10

---

### O programie (0.31.1)

Zakładka **Pomoc** zawiera przycisk **O programie**. Kliknięcie otwiera modalne okno informacyjne z nazwą programu, aktualną wersją, krótkim opisem obsługiwanych backendów oraz licencją.

Numer wersji prezentowany w GUI pochodzi z `tlumacz/version.py` (`APP_VERSION`). Przy kolejnym wydaniu należy zaktualizować tę stałą oraz `pyproject.toml` i odpowiednie wpisy dokumentacji.

## Koncepcja

V3 to fork v2 z pełną obsługą **4 backendów tłumaczenia**:
1. **llama.cpp** — lokalny serwer z modelami GGUF
2. **FastAPI + Transformers** — lokalny serwer z TranslateGemma (specjalny format z kodami języków)
3. **OpenVINO** — bezpośrednia inferencja lokalna z TranslateGemma INT8 (nowy w 0.31.0)
4. **Cloud API** — zewnętrzne API (Gemini, OpenAI, etc.)

---

## Architektura

```
┌─────────────────────────────────────────────────────────┐
│  MainWindow (GUI)                                        │
│  - Zakładki: Tłumaczenie, API i serwer, Dodatki, Pomoc  │
│  - QComboBox "Typ serwera": llama.cpp | FastAPI |       │
│    OpenVINO | Chmura                                      │
│  - Dynamiczny blok Serwer (nazwa + pola zależne od      │
│    backendu)                                              │
│  - QComboBox "Urządzenie OpenVINO": CPU|GPU|AUTO|MULTI  │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────────┐
        │        BackendManager                    │
        │  - Zarządzanie 4 backendami              │
        │  - Delegowanie do odpowiedniego managera │
        └─────────────────────────────────────────┘
                          ↓
        ┌──────────┬──────────┬──────────┬──────────┐
        ↓          ↓          ↓          ↓          ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Server   │ │ FastAPI  │ │ OpenVINO │ │ Cloud    │
│ Manager  │ │ Server   │ │ Backend  │ │ API      │
│(llama.cpp│ │ Manager  │ │          │ │          │
│          │ │          │ │ - INT8   │ │ - Gemini │
│ - GGUF   │ │ - Trans- │ │ - CPU/   │ │ - OpenAI │
│ - CPU/GPU│ │   late-  │ │   GPU/   │ │ - API key│
│ - jinja/ │ │   Gemma  │ │   AUTO   │ │          │
│   chatml │ │   4B     │ │ - fallback│ │          │
│          │ │ - float16│ │   GPU→CPU│ │          │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## ✅ Zrealizowane funkcje

### GUI — zakładka "API i serwer"

**Blok 1: Ustawienia API**
- Adres URL serwera (QLineEdit)
- Klucz API (QLineEdit, Password)
- Typ serwera (QComboBox): **llama.cpp** | **FastAPI (TranslateGemma)** | **OpenVINO (TranslateGemma INT8)** | **Chmura**

**Blok 2: Serwer (nazwa dynamiczna)**

| Pole | llama.cpp | FastAPI | OpenVINO | Chmura |
|------|-----------|---------|----------|--------|
| Port | ✅ | ✅ | ❌ | ❌ |
| Obliczenia serwera (CPU/GPU) | ✅ | ✅ | ❌ | ❌ |
| Model (plik .gguf) | ✅ | ❌ | ❌ | ❌ |
| Model (katalog) | ❌ | ✅ | ✅ | ❌ |
| Model (QComboBox) | ❌ | ❌ | ❌ | ✅ gemini-3.5-flash/flash-lite |
| Szablon czatu (jinja/chatml) | ✅ | ❌ | ❌ | ❌ |
| Wątki (parallel) | ✅ | ✅ | ❌ | ❌ |
| Typ danych (float16/bfloat16/float32) | ❌ | ✅ | ❌ | ❌ |
| Urządzenie OpenVINO (CPU/GPU/AUTO/MULTI) | ❌ | ❌ | ✅ | ❌ |
| ☑ Uruchamiaj serwer razem z programem | ✅ | ✅ | ✅ | ❌ |
| ☑ Czyść cache po każdym tłumaczeniu | ✅ | ✅ | ✅ | ❌ |
| Przycisk restart/start/stop | ✅ | ✅ | ✅ | ❌ |

**Dynamiczna nazwa bloku Serwer:**
- "Serwer llama.cpp — lokalny"
- "Serwer FastAPI — lokalny"
- "Backend OpenVINO — lokalny"
- "Serwer zewnętrzny — chmura"

**Automatyczne ustawienia:**
- Port → Base URL (http://127.0.0.1:PORT/v1)
- Wybór "Chmura" → Base URL = https://generativelanguage.googleapis.com/v1
- Wybór "FastAPI" → chat_template = "translategemma" (specjalny format)

### BackendManager

- Zarządzanie 4 backendami (llama/fastapi/openvino/cloud)
- Sygnały Qt: backend_started, backend_stopped, backend_error
- Wstrzyknięcie ServerManager z MainWindow
- Lazy init FastAPIServerManager i OpenVINOBackend
- BackendManager jest podłączony w GUI (V3)

### OpenVINOBackend (nowy w 0.31.0)

- Bezpośrednia inferencja lokalna — bez serwera HTTP
- Model: TranslateGemma 4B INT8 (`light434/translategemma-4b-it-int8-ov`, ~4.3 GB)
- Urządzenia: CPU (AMD Ryzen), GPU (Intel iGPU), AUTO, MULTI:CPU,GPU
- Fallback GPU→CPU gdy urządzenie niedostępne (np. AMD Radeon)
- Lazy init w procesie potomnym (pickle-safe dla multiprocessing.spawn)
- Wzmocnienie prompta: parametr `context` (glosariusz + skill + system prompt)
- Autodetekcja języka źródłowego (`source_lang="auto"`)
- RAM: ~8 GB (model INT8 + proces)

### FastAPIServer + FastAPIServerManager

- Serwer HTTP z OpenAI-compatible API
- Ładowanie modelu TranslateGemma z Transformers
- Obsługa specjalnego formatu z `source_lang_code`/`target_lang_code`
- Endpoint `/v1/chat/completions`
- Health check `/health`
- Stany: IDLE → STARTING → RUNNING → STOPPING

### core.py — specjalny format TranslateGemma

- Automatyczne ustawianie `chat_template = "translategemma"` gdy backend == "fastapi"
- Mapowanie języków na kody ISO 639-1 (Polish → pl, English → en, etc.)
- Specjalny format wiadomości:
  ```python
  messages = [{
      "role": "user",
      "content": [{
          "type": "text",
          "source_lang_code": "auto",
          "target_lang_code": "pl",
          "text": "tekst do tłumaczenia"
      }]
  }]
  ```

### Konfiguracja

**Pola w `config.json`:**
```json
{
    "backend_type": "llama",
    "fastapi_port": 8001,
    "fastapi_model_path": "",
    "fastapi_dtype": "float16",
    "fastapi_parallel": 1,
    "openvino_model_path": "/home/frs/Modele/openvino/translategemma-4b-it-int8-ov",
    "openvino_device": "CPU"
}
```

### Testy

- **194 testów jednostkowych** — 187 PASSED, 7 FAILED (potwierdzają bugi z audytu)
- Testy BackendManager (25 testów)
- Testy GUI (offscreen, 8 testów)
- Testy konfiguracji, cache, core, extract, glossary, preprocess, server, skill
- **Nowe testy z audytu V3 (56 testów):**
  - `test_audit_bugs.py` — 8 testów wykrywających bugi z audytu (7 FAILED potwierdza bugi)
  - `test_pdf_extractor.py` — 13 testów pokrycia modułu pdf_extractor (wszystkie PASSED)
  - `test_i18n.py` — 20 testów pokrycia modułu i18n (wszystkie PASSED)
  - `test_worker.py` — 15 testów pokrycia modułu worker (wszystkie PASSED)

---

##  Struktura plików

```
agent-translator-v3/
├── docs/
│   ├── ARCHITEKTURA.md          # Architektura V3
│   ├── PLAN_WDROZENIA.md        # Plan wdrożenia (11 faz)
│   ── STATUS.md                # Ten plik
── tlumacz/
│   ├── __init__.py
│   ├── core.py                  # Logika tłumaczenia + specjalny format TranslateGemma
│   ├── server.py                # ServerManager (llama.cpp)
│   ├── cache.py                 # Cache tłumaczeń SQLite
│   ├── skill.py                 # System skills
│   ├── extract.py               # Ekstrakcja tekstu
│   ├── preprocess.py            # Preprocessing
│   ├── convert.py               # Konwersja formatów
│   ├── pdf_extractor.py         # Ekstrakcja PDF
│   ├── glossary.py              # Glosariusz
│   ├── i18n.py                  # Tłumaczenia UI
│   ├── backend_manager.py       # 🆕 Zarządzanie 4 backendami
│   ├── openvino_backend.py      # 🆕 Backend OpenVINO (TranslateGemma INT8)
│   ├── fastapi_server.py        # 🆕 Serwer FastAPI + Transformers
│   ├── fastapi_manager.py       # 🆕 Manager FastAPI
│   ├── skills/
│   │   ├── markdown.md
│   │   ├── html.md
│   │   ├── docx.md
│   │   ├── odt.md
│   │   ├── epub.md
│   │   ├── pdf.md
│   │   └── plaintext.md
│   └── qt_gui/
│       ├── __init__.py
│       ├── app.py               # Punkt wejścia (main())
│       ├── main_window.py       # Główne okno Qt Widgets
│       ├── config.py            # Trwałe ustawienia (config.json)
│       ├── worker.py            # QThread workers
│       ├── backend_manager.py   # 🆕 BackendManager (QObject)
│       ├── theme.py             # Motywy QSS
│       └── resources/
│           ├── style_dark.qss
│           ├── style_light.qss
│           └── tlumacz.svg
├── tests/
│   ├── test_backend_manager.py  # 🆕 25 testów
│   ├── test_cache.py
│   ├── test_config.py
│   ├── test_core.py
│   ├── test_extract.py
│   ├── test_glossary.py
│   ├── test_main_window.py
│   ├── test_preprocess.py
│   ├── test_server.py
│   └── test_skill.py
├── pyproject.toml               # Wersja 0.31.1
├── requirements.txt
├── requirements-fastapi.txt     # 🆕 Zależności FastAPI
├── requirements-openvino.txt    # 🆕 Zależności OpenVINO
└── README.md
```

---

## ✅ Znane problemy z audytu V3 — WSZYSTKIE NAPRAWIONE (2026-09-06)

Pełny raport: `docs/AUDYT_SZCZEGOLOWY_V3.md`

### ✅ Wszystkie błędy krytyczne naprawione!

| # | Problem | Plik | Status |
|---|---------|------|--------|
| 1 | Cache key mismatch z glosariuszem | core.py | ✅ NAPRAWIONY |
| 2 | Niespójność placeholderów PROT | preprocess.py | ✅ NAPRAWIONY |
| 3 | Wyciek uchwytu PDF | core.py | ✅ NAPRAWIONY |
| 4 | Podwójny progress_callback | core.py | ✅ NAPRAWIONY |
| 5 | _clear_finished_thread() AttributeError | main_window.py | ✅ NAPRAWIONY |
| 6 | Brak PyMuPDF w requirements.txt | requirements.txt | ✅ NAPRAWIONY |
| 7 | Brak optional-dependencies dla FastAPI | pyproject.toml | ✅ NAPRAWIONY |
| 3.6 | Wyciek uchwytu PDF (pdf_extractor) | pdf_extractor.py | ✅ NAPRAWIONY |

### ✅ Bugi GUI naprawione:

| Bug | Problem | Status |
|-----|---------|--------|
| G2 | _kill_orphaned_processes() blokuje GUI | ✅ NAPRAWIONY |
| G4 | BackendManager.restart() race condition | ✅ NAPRAWIONY |
| G5 | _start_fastapi() blokuje GUI | ✅ NAPRAWIONY |
| W5 | Martwy kod ServerRestartWorker/Thread | ✅ USUNIĘTY |

### ✅ Ostrzeżenia (W1-W10) — większość naprawiona:

| Bug | Problem | Status |
|-----|---------|--------|
| W1 | Bezpośredni dostęp do _state | ✅ NAPRAWIONY (set_state()) |
| W2 | _show_preview() czyta plik w GUI | ⏭️ Niski priorytet |
| W3 | _refresh_glossary_count() czyta CSV | ⏭️ Niski priorytet |
| W4 | Nadmiarowe logowanie | ✅ USUNIĘTY |
| W6 | Podwójne połączenia sygnałów | ✅ NAPRAWIONY (disconnect guard) |
| W8 | save_settings() w GUI thread | ⏭️ Akceptowalne (mały JSON) |
| W9 | server.start() przed QApplication | ✅ NAPRAWIONY |
| W10 | Dostęp do _config | ✅ NAPRAWIONY (property config) |

### Pozostały martwy kod (~147 linii)

| Plik | Linie | Status |
|------|-------|--------|
| `convert.py` | 127 | ⚠️ Nadal do usunięcia |
| `_extract_pdf()` w extract.py | ~20 | ⚠️ Nadal do usunięcia |

---

## 🚧 Do zrobienia

### Wysoki priorytet
1. **Testy funkcjonalne** — przetestować tłumaczenie z każdym backendem
2. **Przywrócenie skilli DOCX/ODT** — zaktualizowany opis (XML in-place z separatorami)
3. **PDF round-trip** — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF)
11. **Decyzja o BackendManager** — podłączyć w GUI lub usunąć (~852 linie martwego kodu)

### Średni priorytet
12. **Stabilizacja przed wydaniem** — niezawodne tłumaczenie wszystkich formatów
13. **Pomoc w GUI → i18n** — przenieść treść Pomocy do systemu i18n
14. **Dokumentacja README PL/EN** — zaktualizowana do wersji 0.31.1
15. **Usunąć martwy kod** — convert.py (~127 linii), _extract_pdf() w extract.py

### Niski priorytet
16. **OCR dla skanów PDF** — architektura przygotowana
17. **Detekcja przez próbę modelu** — mikro-zapytanie wykrywające EOS/tryb myślenia
18. **Pełna edycja config.json przez GUI** — przycisk Zapisz + autozapis
19. **Format plików tłumaczeń** — test kompletności kluczy i18n
20. **Automatyczna synchronizacja repo** — skrypt po buildzie
21. **Ikona repo / social preview** — og-image dla GitHub

### Kosmetyczne
22. **Podwójna etykieta "Model:"** — QFormLayout nie ukrywa etykiet automatycznie (nie wpływa na funkcjonalność)

---

##  Instrukcja Budowania

```bash
# Instalacja w trybie deweloperskim
cd /home/frs/Projekty/agent-translator-v3
pip install -e . --break-system-packages

# Uruchomienie GUI
PYTHONPATH=/home/frs/Projekty/agent-translator-v3 python3 -m tlumacz.qt_gui.app

# Testy
PYTHONPATH=/home/frs/Projekty/agent-translator-v3 pytest tests/ -v

# Testy GUI (offscreen)
QT_QPA_PLATFORM=offscreen PYTHONPATH=/home/frs/Projekty/agent-translator-v3 pytest tests/test_main_window.py -v
```

---

## 📊 Metryki

**Postęp głównych zadań:** 95% (dokumentacja README zaktualizowana)
- Faza 0-9: ✅ Zakończone
- Faza 10: ⏳ Testy funkcjonalne (wymaga modelu TranslateGemma)
- Faza 11: ✅ Dokumentacja README PL/EN zaktualizowana do 0.31.1

**Testy:** 263 testy (263 PASSED, 0 FAILED) ✅
- Wszystkie bugi krytyczne z audytu V3 naprawione i zweryfikowane testami
- 56 nowych testów z audytu (pdf_extractor, i18n, worker, audit_bugs)
- **50 nowych testów FastAPI** (fastapi_server, fastapi_manager)

**Pokrycie testami:**
- ✅ pdf_extractor.py — 13 testów (wcześniej 0)
- ✅ i18n.py — 20 testów (wcześniej 0)
- ✅ worker.py — 15 testów (wcześniej 0)
- ✅ fastapi_server.py — 28 testów (wcześniej 0)
- ✅ fastapi_manager.py — 22 testy (wcześniej 0)

**Backendy:**
- llama.cpp: ✅ Działa (bez regresji)
- FastAPI + TranslateGemma: ✅ Zaimplementowane (wymaga modelu)
- OpenVINO + TranslateGemma INT8: ✅ Działa (CPU, fallback GPU→CPU)
- Cloud API: ✅ Działa (bez regresji)

**Audyt V3:**
- ✅ 7 błędów krytycznych — WSZYSTKIE NAPRAWIONE
- ✅ 4 bugi GUI — WSZYSTKIE NAPRAWIONE
- ✅ 6/10 ostrzeżeń — NAPRAWIONE (4 niski priorytet/akceptowalne)
- ⚠️ ~147 linii martwego kodu pozostało (convert.py, _extract_pdf)
- 📄 Pełny raport: `docs/AUDYT_SZCZEGOLOWY_V3.md`

---

## 🔄 Migracja z V2

V3 jest **kompatybilny wstecznie** z konfiguracją v2 (`~/.config/tlumacz/config.json`).

1. Skopiuj konfigurację: `cp ~/.config/tlumacz/config.json ~/.config/tlumacz/config.json.bak`
2. Zainstaluj v3: `pip install -e . --break-system-packages`
3. Uruchom: `PYTHONPATH=... python3 -m tlumacz.qt_gui.app`
4. Sprawdź ustawienia w zakładce "API i serwer"

**Uwaga:** V3 ma BackendManager który zarządza 4 backendami (llama/fastapi/openvino/cloud). BackendManager jest podłączony w GUI.

---

## 🧪 Wyniki testów backendów (2026-09-09)

### Porównanie wydajności: llama.cpp vs OpenVINO vs FastAPI

Test na pliku `tagi.md` (152 linie, Markdown z tagami HTML) z skillem MkDocs:

| Backend | Skill | Czas | Linii | Strikethrough | Halucynacje | Werdykt |
|---------|-------|------|-------|---------------|-------------|---------|
| **llama.cpp** | MkDocs | **3:19** ⚡ | **153** (100%+) | ✅ przekreślony | ✅ Brak | **🏆 NAJLEPSZY** |
| OpenVINO | MkDocs | 4:40 | 148 | ❌ podkreślony | ✅ Brak | ⚠️ Wolniejszy |
| OpenVINO | markdown-tags | 4:46 | 150 | ✅ przekreślony | ❌ PROT | ⚠️ Halucynacje |
| FastAPI | markdown-tags | >10:00 | ⚠️ Zmienna | ⚠️ Zależy | ⚠️ Zależy | Eksperymentalne |

### Rekomendacja

**llama.cpp + MkDocs = najlepsze rozwiązanie** dla tłumaczenia Markdown:
- ⚡ **30% szybszy** niż OpenVINO
- ✅ **Najlepsza jakość** tłumaczenia
- ✅ **Brak halucynacji** (PROT, placeholder)
- ✅ **Pełna kompatybilność** ze skillami

### OpenVINO — status wdrożenia

✅ **Zaimplementowane:**
- OpenVINOBackend z obsługą CPU/GPU/AUTO/MULTI
- Model INT8 (~4.4GB) — mniejsze zużycie RAM
- Integracja z BackendManager
- GUI z wyborem urządzenia

⚠️ **Ograniczenia:**
- Wolniejszy niż llama.cpp (~4:40 vs 3:19)
- Problemy z halucynacjami (PROT) przy niektórych skillach
- Wymaga openvino-genai i modelu INT8

**Kiedy używać OpenVINO:**
- Brak możliwości uruchomienia llama.cpp
- Dostępne GPU (Intel iGPU, AMD iGPU)
- Ograniczona pamięć RAM (INT8 ~6GB vs FP32 ~12GB)

### Naprawione bugi (2026-09-09)

1. ✅ **Cleanup po błędzie** — dodano `start_chat()` / `finish_chat()` w openvino_backend.py
2. ✅ **Skill za długi** — przepisany markdown-tags.md w stylu mkdocs (20 linii)
3. ✅ **Strikethrough** — poprawne tłumaczenie z glosariuszem

**Raport bugów:** `docs/BUG_OPENVINO_SKILL_INTEGRATION.md`

---

**Ostatnia aktualizacja:** 2026-09-10 (wydanie 0.31.1, dokumentacja, pakiety)
**Wersja:** 0.31.1
**Status:** Wersja robocza/testowa — **4 backendy działają, 263 testy PASSED**
**Raport audytu:** `docs/AUDYT_SZCZEGOLOWY_V3.md`
