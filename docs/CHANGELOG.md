# Dziennik zmian

Wszystkie znaczące zmiany w tym projekcie są dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/),
projekt przestrzega [Semantic Versioning](https://semver.org/lang/pl/).

## [0.31.1] - 2026-09-10

### Dodano
- **O programie** w zakładce Pomoc — wyskakujące okno pokazuje nazwę programu, wersję `0.31.1`, opis oraz licencję.
- **Centralne metadane wersji** w `tlumacz/version.py`, wykorzystywane przez GUI.

### Testy
- Dodano test GUI dla okna „O programie” w języku polskim i angielskim.
- Zaktualizowano test DOC-01: wersja w `QWEN.md` musi być zgodna z `pyproject.toml`.

### Dokumentacja
- `QWEN.md`, `docs/STATUS.md` i dokumentacja wydania zostały zaktualizowane do `0.31.1`.

- przygotowano artefakty pakietów Arch, Debian, RPM/SRPM i AppImage;
- dodano raport budowania oraz sumy SHA-256.

## [Niewydane]

### Bugi znalezione podczas testów OpenVINO (2026-09-07)
- **GUI: Log nie wyświetla postępu tłumaczenia** — log pokazuje tylko początkowe informacje, nie pokazuje ukończonych bloków
- **GUI: Podwójny reset OpenVINO** — przy przełączaniu na OpenVINO, reset serwera następuje 2 razy jeden po drugim
- **GUI: Pole Klucz API widoczne przy OpenVINO** — powinno być ukryte (OpenVINO nie używa klucza API)
- **OpenVINO: Tłumaczy tagi Markdown** — mimo instrukcji w skillu, model tłumaczy tagi które powinny być zachowane
- **OpenVINO: Nie tłumaczy sekcji niemieckiej** — problem z wielojęzycznością (tylko EN i FR tłumaczone)
- **llama.cpp: Brak specjalnego formatu TranslateGemma** — llama.cpp nie obsługuje formatu z kodami języków (`source_lang_code`, `target_lang_code`)

### Planowane
- **PDF round-trip** — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR)
- **Skille DOCX/ODT** — przywrócenie z zaktualizowanym opisem (XML in-place z separatorami)
- **Stabilizacja przed wydaniem** — niezawodne tłumaczenie wszystkich formatów
- **Pomoc w GUI → i18n** — przeniesienie treści Pomocy do systemu i18n
- **Dokumentacja README PL/EN** — aktualizacja do wersji v3 (0.31.0)
- **Usunąć martwy kod** — convert.py (~127 linii), _extract_pdf() w extract.py
- **Naprawić log GUI** — wyświetlanie postępu tłumaczenia (ukończone bloki)
- **Naprawić podwójny reset OpenVINO** — debounce lub sprawdzenie czy backend już działa
- **Naprawić widoczność pola Klucz API** — ukryć przy OpenVINO
- **Konfiguracja FastAPI** — przetestować i skonfigurować backend FastAPI
- **Test z większym plikiem** — `skille.md` (114KB) dla porównania wydajności

## [0.31.0] - 2026-09-07

### Dodano — Backend OpenVINO

**Nowy backend tłumaczenia: OpenVINO (TranslateGemma 4B INT8)** — czwarty backend obok llama.cpp, FastAPI i Cloud API. Bezpośrednia inferencja lokalna bez serwera HTTP, model ładowany do RAM, tłumaczenie przez OpenVINO Runtime zoptymalizowane pod CPU AMD/Intel.

#### Nowe pliki
- `tlumacz/openvino_backend.py` — klasa `OpenVINOBackend` z `VLMPipeline`
- `requirements-openvino.txt` — zależności (`openvino`, `openvino-genai`)

#### Architektura
- Bezpośrednie wywołanie `OpenVINOBackend.translate()` z `core.py._translate_chunk()`
- Lazy init w procesie potomnym (pickle-safe dla `multiprocessing.spawn`)
- Parametry `openvino_model_path` i `openvino_device` w `TranslatorConfig`
- Automatyczny fallback GPU→CPU gdy urządzenie niedostępne (np. AMD iGPU)

#### Integracja z BackendManager
- `BackendConfig` rozszerzony o `openvino_model_path`, `openvino_device`
- `_VALID_BACKENDS` = `("llama", "cloud", "fastapi", "openvino")`
- Metody `start()`, `stop()`, `is_running()`, `get_base_url()` obsługują openvino
- `stop_openvino()` — zatrzymuje backend niezależnie od aktywnego wyboru
- `_get_openvino_backend()` — lazy init z obsługą błędów

#### GUI
- QComboBox "Typ serwera" — nowa pozycja: **"OpenVINO (TranslateGemma INT8)"**
- QComboBox **"Urządzenie OpenVINO"**: CPU, GPU (iGPU), AUTO, Hybrydowy CPU+GPU
  - Widoczne TYLKO gdy wybrano backend OpenVINO
  - Tooltip informuje o fallback na CPU gdy GPU niedostępne
- Dynamiczny blok Serwer: nazwa "Backend OpenVINO — lokalny"
- Placeholder/tooltip dla ścieżki modelu OpenVINO IR
- Port, obliczenia serwera, wątki — ukryte (nie dotyczą OpenVINO)
- Checkboxy auto-start i cache — widoczne

#### Wzmocnienie prompta
- `translate()` przyjmuje parametr `context` (glosariusz + skill + system prompt)
- `_build_prompt()` wstawia kontekst między instrukcję a tekst
- `core.py` przekazuje `system_prompt` jako `context`
- **Efekt:** glosariusz i skill (Markdown/HTML/DOCX) działają z OpenVINO

#### Naprawione błędy
- `_clean_output()` — nie ucina już wieloliniowych tłumaczeń (usunięto `lines[0]`)
- `APIConnectionError` — OpenVINO nie próbuje łączyć się przez HTTP
- Cytaty `**text**` i `"text"` — precyzyjniejsze wykrywanie (`count() == 2`)

#### Konfiguracja
Nowe pola w `AppSettings` i `config.json`:
```json
{
    "openvino_model_path": "/home/frs/Modele/openvino/translategemma-4b-it-int8-ov",
    "openvino_device": "CPU"
}
```

#### Zależności
`pyproject.toml` — optional-dependencies:
```toml
[project.optional-dependencies]
openvino = [
    "openvino>=2024.6.0",
    "openvino-genai>=2024.6.0",
]
```

#### Wydajność (AMD Ryzen 7 5825U, CPU, model INT8)
| Metryka | Wartość |
|---------|---------|
| Ładowanie modelu | ~3s |
| Tłumaczenie krótkie (~30 znaków) | ~5s |
| Tłumaczenie średnie (~100 znaków) | ~6s |
| Tłumaczenie długie (~1800 znaków) | ~116s |
| RAM | ~8 GB |
| Autodetekcja języka | ✅ (source_lang="auto") |

#### Ograniczenia
- OpenVINO GPU plugin wspiera **Intel iGPU** — AMD Radeon nie działa (fallback na CPU)
- Brak wsparcia dla NPU
- Model text-only (vision stub w modelu nie działa)

#### Testy
- **192 testy PASSED, 0 FAILED** — brak regresji
- Testy integracyjne: en→pl, de→pl, długi tekst, BackendManager start/stop
- Test fallback GPU→CPU na AMD iGPU

## [0.30.0] - 2026-09-06

### Dodane
- **BackendManager** — centralny zarządca trzech backendów (llama.cpp, Cloud, FastAPI) — podłączony w GUI
- **QComboBox "Typ serwera"** — wybór backendu w GUI
- **Dynamiczne pole "Model"** — placeholder/tooltip zmienia się w zależności od backendu
- **Persystencja ścieżki modelu** — każdy backend pamięta swoją ścieżkę
- **FastAPI + Transformers** — obsługa TranslateGemma (specjalny format z kodami języków)
- **FastAPIStartWorker** — ładowanie modelu Transformers w osobnym wątku (nie blokuje GUI)
- **Cache clearing przy restarcie** — przycisk "Restart serwera" czyści cache tłumaczeń
- 36 nowych testów jednostkowych (BackendManager)

### Naprawione
- **G1:** `_clear_finished_thread()` — AttributeError (`isRunning()` → `_is_thread_running()`)
- **G2:** `_kill_orphaned_processes()` — blokada GUI (usunięto, duplikat)
- **G3:** `_on_restart_server()` — blokada GUI ~10s (usunięto `wait()`)
- **G4:** `BackendManager.restart()` — race condition (deleguje do ServerManager/FastAPIServerManager)
- **G5:** `BackendManager._start_fastapi()` — blokada GUI (przeniesiono do FastAPIStartWorker)
- **G6:** `ServerRestartWorker`/`ServerRestartThread` — martwy kod (usunięto)
- **#2.1:** Cache key mismatch z glosariuszem (przeniesiono przed `cache.get()`)
- **#2.2:** Niespójność placeholderów PROT (`[PROT_N]` → `⟦PROT_N⟧`)
- **#2.3:** Wyciek uchwytu PDF (dodano `try/finally` z `doc.close()`)
- **#2.4:** Podwójny `progress_callback` w trybie równoległym
- **#2.5:** Brak PyMuPDF w `requirements.txt` (dodano `PyMuPDF>=1.24.0`)
- **#2.6:** Brak `optional-dependencies` dla FastAPI w `pyproject.toml`
- **#2.7:** Wyciek uchwytu PDF w `pdf_extractor.py` (dodano `try/finally`)
- **#3.1:** "Brak konfiguracji serwera" — `ServerManager._config` jest None (ZAWSZE tworzy z config)
- **#3.2:** QThread crash przy auto-start (sprawdza `backend_type` i `server_gguf_path`)
- **#3.3:** HF_TOKEN nie dostępne w procesie Python (ładuje z `~/.bashrc`)
- **#3.4:** FastAPI 401 Unauthorized (przekazuje token do `from_pretrained()`)
- **#3.5:** FastAPI server crash przy restarcie (ładowanie modelu w osobnym wątku)
- **#3.6:** Przekroczenie limitu ctx_size (zmniejszono `chunk_size` do 1200)
- **#3.7:** Ścieżka do modelu znika przy przełączaniu backendów (nie nadpisuje pustą wartością)
- **#4.1:** Tłumaczenie zawiera tylko 1/3 tekstu (dodano instrukcję do skill Markdown)
- **#4.2:** Model powtarza prompt zamiast tłumaczyć (uproszczono prompt systemowy)
- **#4.3:** Konflikt skilli (wyłączono `mkdocs-translations.md` i `txt-translategemma.md`)

### Zmienione
- Usunięto szablon czatu "translategemma" z llama.cpp (nieobsługiwany format)
- Przycisk serwera uproszczony do "Restart serwera" (był wielofunkcyjny start/stop/restart)
- Prompt systemowy uproszczony do "Przetłumacz poniższy tekst na {target_language}"
- Skill Markdown: dodano "Tłumacz WSZYSTKIE fragmenty tekstu, niezależnie od języka źródłowego"
- Wersja: 0.21.2 → 0.21.2 (bez zmian numeru wersji)

### Zarchiwizowane dokumenty
- `docs/PLAN_WDROZENIA_TRANSFORMERS_BACKEND.md` → `docs/archive/`
- `docs/TRANSLATEGEMMA_FULL_GUIDE.md` → `docs/archive/`
- `docs/STATUS_FASTAPI.md` → `docs/archive/`
- `docs/wdrozenie-fastapi-transformers.md` → `docs/archive/`

### Znane ograniczenia
- **Jakość tłumaczenia:** Model `Hy-MT2-1.8B` (1.8B) jest niestabilny — rekomendowany większy model (7B+)
- **Limit ctx_size:** Model ma limit 4096 tokenów — `chunk_size` musi być ≤1200 znaków
- **Konfiguracja:** GUI musi być uruchamiane z v3 (nie v2) — problem z `sys.path`

### Planowane
- **PDF round-trip** — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR)
- **Stabilizacja przed wydaniem** — niezawodne tłumaczenie wszystkich formatów
- **Pomoc w GUI → i18n** — przeniesienie treści Pomocy do systemu i18n
- **Dokumentacja README PL/EN** — aktualizacja do wersji v2 (0.21.0)
- Testowanie nowszych modeli 2B i wzmocnienie promptów dla Markdown/HTML/DOCX/ODT/EPUB
- Optymalizacja wydajności tłumaczenia i wybór finalnego modelu jakość/szybkość

## [0.20.1] - 2026-09-04

### Dodane
- **ServerManager** — centralny zarządca serwera z maszyną stanów (IDLE/STARTING/RUNNING/STOPPING)
- **Inteligentny przycisk serwera** — 4 stany: restart/stop/start/info
- **Tłumaczenie w chmurze** — QComboBox modeli (cloud + LOCAL + ręczny)
- **Szablony czatu** — jinja/chatml/translategemma
- **Języki "wykryj do X"** — automatyczna detekcja języka źródłowego
- **Auto-select skill** — odznacza poprzednie, zaznacza pasujący do pliku
- **Cloud models** — wczytywanie z cloud_models.json (gemini-3.5-flash, gemini-3.5-flash-lite)
- **LOCAL pamięta ustawienia** — last_local_base_url, last_local_api_key

### Naprawione
- Crash przy anulowaniu tłumaczenia (`QThread: Destroyed while thread is still running`)
- Race conditions w ServerManager (restart z IDLE, cleanup thread)
- `_on_operation_success` — rozróżnianie restartu od stopu
- `_cleanup_thread` — usunięcie pętli QTimer, bezpośrednie połączenie thread.finished

### Zmienione
- Pole modelu: QLineEdit → QComboBox (editable)
- Języki docelowe: nazwy (Polish, English) → "wykryj do X" (wykryj do pl, wykryj do en)
- Szablony czatu: Auto/chatml → jinja/chatml/translategemma
- Wersja: 0.20.1 → 0.21.0-dev

### Testy
- 102 testy jednostkowe — wszystkie przechodzą
- Testy ServerManager (stan, kolejka, restart)
- Testy GUI (offscreen)

## [0.19.1] - 2026-08-23

### Dodane
- Test build z aktualnym pipeline tłumaczenia dokumentów i round-trip DOCX/ODT/EPUB
- Stoper tłumaczenia — zaimplementowany i zachowany w GUI
- Lokalna paczka Arch `tlumacz-0.19.1-1-any.pkg.tar.zst` zbudowana pomyślnie

### Zmienione
- Lokalna paczka dodana do `/home/frs/RepoArch/x86_64/moje-repo.db`
- Aktualny model testowy: **Hy-MT2-1.8B-Q4_K_S** — szybki ale problemy z jakością dla dokumentów wielojęzycznych

### Notatki
- **0.19.1 to wczesna wersja rozwojowa/testowa, celowo nie publikowana w publicznym AUR**
- Utworzono snapshot/tag `snapshot-20260823-pre-aur` przed eksperymentami z modelami
- Testy formatów pokazują że struktura round-trip DOCX/ODT/EPUB jest zachowana; problemy to jakość tłumaczenia/model

## [0.19.0] - 2026-08-20

### Dodane
- **DOCX i ODT round-trip** — tłumaczenie do oryginalnego formatu zamiast Markdown
- Tłumaczone są tylko węzły tekstowe (`w:t` dla DOCX, `text:*` dla ODT)
- Znaczniki, style, tabele i pliki nietreściowe są zachowywane

### Zmienione
- Znaczniki XML/HTML chronione przed URL-ami (w tym URL-e w atrybutach)
- Chunkowanie XML/HTML po znakach bez rozcinania chronionych placeholderów
- Pliki XML bez tekstu kopiowane verbatim zamiast wysyłania do modelu

## [0.18.2] - 2026-08-20

### Zmienione
- Ekstrakcja DOCX używa **tylko pandoc**, usunięto zależność python-docx i fallback LibreOffice

## [0.18.1] - 2026-08-20

### Naprawione
- EPUB nie stosuje już wzorców pomijania Markdown/YAML do treści książki
- Tokeny kontrolne szablonu czatu usuwane z przetłumaczonego wyjścia

## [0.18.0] - 2026-08-20

### Dodane
- Round-trip tłumaczenie EPUB z zachowaniem struktury XHTML i plików nietreściowych

### Naprawione
- Przebudowa EPUB nie reserializuje już XML ani nie polega na kruchym podziale akapitów

## [0.17.2] - 2026-08-19

### Naprawione
- Ekstrakcja DOCX działa bez python-docx w venv aplikacji (używa pandoc)

## [0.17.1] - 2026-08-19

### Naprawione
- Dokumenty dwujęzyczne/wielojęzyczne jawnie instruują model do tłumaczenia każdego fragmentu niebędącego w języku docelowym

## [0.17.0] - 2026-08-19

### Dodane
- Obsługa dokumentów binarnych: PDF, DOCX, ODT, EPUB
- Szablon skilla użytkownika i `skip_patterns` w frontmatterze
- Fallback szablonu czatu modelu i trwałe `model_profiles`
- Akcja przywracania domyślnych z backupami konfiguracji
- Tooltipy GUI i pomoc parametrów

## [0.16.0] - 2026-08-19

### Dodane
- Ochrona kodu/URL, konfigurowalne wzorce pomijania, chunkowanie świadome sekcji
- Wsparcie `server_chat_template` dla jinja vs chatml
- Czyszczenie tokenów EOS szablonu czatu

## [0.15.0] - 2026-08-19

### Dodane
- Wsparcie zarządzanego serwera dla modeli myślących, `--jinja`, `--ctx-size 8192`, `enable_thinking: false`, `max_tokens` 6000

## [0.14.0] - 2026-08-19

### Dodane
- Akcje odświeżania i importu skilli użytkownika; ukryte pliki dostępne w dialogach plików

## [0.13.0] - 2026-08-19

### Dodane
- Skille użytkownika z `~/.config/tlumacz/skills/`, nadpisujące wbudowane skille po nazwie

## [0.12.0] - 2026-08-19

### Dodane
- Zakładki Tłumaczenie / Ustawienia / Pomoc i wbudowana pomoc PL/EN

## [0.11.0] - 2026-08-19

### Dodane
- Wstrzykiwanie skilli specyficznych dla formatu i początkowy zestaw testów

## [0.10.0] - 2026-08-19

### Dodane
- Ustawienia lokalnego serwera w GUI i własny prompt tłumaczenia

## [0.9.0] - 2026-08-19

### Dodane
- Walidacja konfiguracji z ostrzeżeniami widocznymi dla użytkownika

## [0.8.0] - 2026-08-19

### Zmienione
- Wykrywanie tekstu już napisanego w języku docelowym oparte na prompcie

## [0.7.0] - 2026-08-19

### Dodane
- Wsparcie glosariusza CSV i zarządzanie glosariuszem w GUI

## [0.6.0] - 2026-08-19

### Dodane
- Przełączanie motywów system/jasny/ciemny

## [0.5.1] - 2026-08-19

### Dodane
- Zarządzany lokalny proces `llama-server` i pola konfiguracji serwera

## [0.5.0] - 2026-08-18

### Dodane
- Początkowe GUI Qt/PySide6, worker tłumaczenia w tle, trwała konfiguracja, wielokrotny silnik tłumaczenia i pliki pakowania

## [0.4.0] - 2025-06-20

### Dodane
- Wyświetlanie statusu wywołania narzędzi i komunikatów wyników narzędzi w CLI

## [0.1.0] - 2025-06-20

### Dodane
- Początkowy Translator Agent CLI z React + Ink, historią wiadomości, linią statusu, komendami wyjścia i strukturą projektu TypeScript/ESM
