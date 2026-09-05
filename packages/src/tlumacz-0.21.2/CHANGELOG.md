# Dziennik zmian

Wszystkie znaczące zmiany w tym projekcie są dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/),
projekt przestrzega [Semantic Versioning](https://semver.org/lang/pl/).

## [Niewydane]

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
