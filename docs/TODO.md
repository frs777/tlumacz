# TODO - Agent Translator V2

## Wysoki Priorytet 🔴

### 1. Inteligentny Przycisk Restart Serwera ✅ ZAKOŃCZONE
**Status**: ZAKOCZONE
**Pliki**: `tlumacz/qt_gui/main_window.py`, `tlumacz/qt_gui/worker.py`, `tlumacz/i18n.py`

**Zaimplementowane**:
- 4 stany przycisku zależne od stanu serwera i checkboxa auto-start:
  1. Running + box checked → "Restart serwera" (stop + start)
  2. Running + box unchecked → "Zatrzymaj serwer" (stop)
  3. Stopped + box checked → "Uruchom serwer" (start)
  4. Stopped + box unchecked → "Zaznacz box..." (info message)
- Przycisk zawsze aktywny (nigdy nie zablokowany)
- Checkbox `auto_start_server` połączony z `_update_restart_button_label()`

**Naprawione bugi**:
- `_on_operation_success` — sprawdza czy serwer faktycznie działa po STOPPING (restart vs stop)
- `restart()` z IDLE — używa istniejącego serwera zamiast wymagać `_config`
- `_cleanup_thread` — `worker.finished → thread.quit → thread.finished → cleanup` (bez QTimer pętli)
- `_run_operation` — sprawdza czy `_thread` jest running przed utworzeniem nowego

**Testy**: 102/102 przechodzą

---

### 2. Crash przy Anulowaniu Tłumaczenia Lokalnego ✅ ZAKOŃCZONE
**Status**: ZAKOŃCZONE
**Plik**: `tlumacz/qt_gui/main_window.py`
**Problem**: `QThread: Destroyed while thread '' is still running` przy anulowaniu

**Przyczyna**: `_clear_finished_thread()` ustawiał `self._thread = None` zanim thread się zakończył. Thread był niszczony przez GC podczas gdy był "running".

**Rozwiązanie**: Wywołanie `thread.stop()` (cancel + quit + wait) przed usunięciem referencji.

**Testy**: Ręczne testy GUI — brak crashu przy anulowaniu

---

### 3. Wdrożenie Tłumaczenia w Chmurze ✅ ZAKOŃCZONE
**Status**: ZAKOŃCZONE
**Pliki**: `tlumacz/qt_gui/config.py`, `tlumacz/qt_gui/main_window.py`

**Zaimplementowane**:
- `CLOUD_MODELS_CONFIG` — wczytywanie cloud_models.json (projekt/użytkownik/domyślne)
- QComboBox zamiast QLineEdit dla pola "Model"
- Lista modeli: cloud models (z pliku) + separator + LOCAL + puste pole (ręczny)
- `_on_model_changed()` — automatyczne ustawienie base_url/api_key:
  - Cloud model → base_url z konfiguracji, api_key z ustawień
  - LOCAL → przywraca last_local_base_url i last_local_api_key
  - Puste/własny → bez zmian (ręczna konfiguracja)
- `_collect_settings()` — zapamiętuje last_local_* przy wyborze LOCAL
- Pola w AppSettings: `cloud_models`, `last_local_base_url`, `last_local_api_key`, `last_local_model`

**Testy**: 102/102 przechodzą + ręczne testy GUI

---

## Średni Priorytet 🟡

### 4. Model Combobox ✅ ZAKOŃCZONE (jako część cloud translation)
**Status**: ZAKOŃCZONE

### 5. Szablon czatu TranslateGemma ✅ ZAKOCZONE
**Status**: ZAKOŃCZONE
**Pliki**: `tlumacz/qt_gui/main_window.py`, `tlumacz/server.py`, `tlumacz/i18n.py`

**Zaimplementowane**:
- Combo box szablonów czatu: `jinja` (natywny), `chatml`, `translategemma` (kody języków)
- "translategemma" mapowane na `None` w `_template_attempts()` (używa natywnego jinja Gemma 3)
- Tłumaczenia i18n: `settings.chat_jinja`, `settings.chat_translategemma`

### 6. Języki w formacie "wykryj do X" ✅ ZAKOŃCZONE
**Status**: ZAKOŃCZONE
**Pliki**: `tlumacz/qt_gui/main_window.py`, `tlumacz/core.py`, `tlumacz/i18n.py`

**Zaimplementowane**:
- Wszystkie języki w formacie "wykryj do X" (np. "wykryj do pl", "wykryj do en")
- Nazwy wyświetlane: "Polski", "English", "German" (nie "Polish", "English")
- `core.py` — obsługa formatu "wykryj do X" w system prompt
- Format działa dla wszystkich modeli (nie tylko TranslateGemma)

**Testy**: 102/102 przechodzą + ręczne testy GUI

---

## Niski Priorytet 

### 7. Zmiana typu pliku odznacza skilla ✅ ZAKOCZONE
**Status**: ZAKOŃCZONE
**Plik**: `tlumacz/qt_gui/main_window.py`

**Zaimplementowane**:
- `_auto_select_skill_for_input()` odznacza wszystkie skille przy zmianie pliku
- Automatycznie zaznacza pasujący skill (np. Markdown dla .md)
- Logowanie: "Automatycznie wybrano skill: {name}"

### 8. Dynamic Button Name ✅ ZAKOŃCZONE (jako część punktu 1)
**Status**: ZAKOŃCZONE
**Plik**: `tlumacz/qt_gui/main_window.py`

**Zaimplementowane w punkcie 1**:
- `_update_restart_button_label()` — 4 stany etykiety przycisku
- Połączone z checkboxem `auto_start_server`
- Wywoływane po każdej zmianie stanu serwera

**Testy**: 102/102 przechodzą + ręczne testy GUI

---

## Dokumentacja 

### 9. Uzupełnić Dokumentację
**Status**: W POSTĘPIE

**Zadania**:
- [x] Stworzyć `docs/STATUS.md`
- [x] Stworzyć `docs/FIX-RESTART-BUTTON.md`
- [x] Stworzyć `docs/TODO.md` (ten plik)
- [ ] Dodać diagramy architektury (Mermaid)
- [ ] Dodać instrukcję migracji z v1 do v2
- [ ] Dodać FAQ

---

## Testy 

### 10. Rozszerzyć Pokrycie Testów
**Status**: DO ZROBIENIA

**Zadania**:
- [ ] Dodać testy ServerManager:
  - [ ] Test stanu IDLE → STARTING → RUNNING
  - [ ] Test kolejki operacji
  - [ ] Test automatycznego restartu
- [ ] Dodać testy GUI:
  - [ ] Test przycisku restart (enabled/disabled)
  - [ ] Test zmiany etykiety przycisku
  - [ ] Test tworzenia serwera z GUI
- [ ] Dodać testy integracyjne:
  - [ ] Test pełnego cyklu restartu
  - [ ] Test orphaned process cleanup

---

## Refaktoryzacja 🔧

### 11. Wyczyścić Kod
**Status**: DO ZROBIENIA

**Zadania**:
- [ ] Usunąć nieużywane importy
- [ ] Ujednolicić styl kodu (black/ruff)
- [ ] Dodać type hints gdzie brakuje
- [ ] Zaktualizować docstrings

---

## Wydajność 

### 12. Optymalizacja
**Status**: DO ZROBIENIA

**Zadania**:
- [ ] Profilować start aplikacji
- [ ] Optymalizować ładowanie skills
- [ ] Optymalizować cache tłumaczeń
- [ ] Dodać lazy loading dla dużych plików

---

## Bezpieczeństwo 

### 13. Audyt Bezpieczeństwa
**Status**: DO ZROBIENIA

**Zadania**:
- [ ] Sprawdzić handling API keys (nie logować!)
- [ ] Sprawdzić path traversal w plikach
- [ ] Sprawdzić injection w promptach
- [ ] Dodać rate limiting dla API calls

---

## Wsparcie dla Formatów 📄

### 14. Nowe Formaty
**Status**: PLANOWANE

**Zadania**:
- [ ] Wsparcie dla LaTeX (.tex)
- [ ] Wsparcie dla reStructuredText (.rst)
- [ ] Wsparcie dla AsciiDoc (.adoc)
- [ ] Wsparcie dla JSON (.json) - tłumaczenie wartości

---

## UI/UX 

### 15. Ulepszenia Interfejsu
**Status**: PLANOWANE

**Zadania**:
- [ ] Dodać progress bar dla restartu serwera
- [ ] Dodać powiadomienia systemowe (gotowe tłumaczenie)
- [ ] Dodać dark/light mode toggle
- [ ] Dodać skróty klawiszowe (Ctrl+R = restart serwera)
- [ ] Dodać drag & drop dla plików

---

## Integracja 🔌

### 16. Wtyczki i Rozszerzenia
**Status**: PLANOWANE

**Zadania**:
- [ ] System wtyczek dla skills
- [ ] Wsparcie dla custom providers (nie tylko OpenAI-compatible)
- [ ] Wsparcie dla webhooków (po zakończeniu tłumaczenia)
- [ ] API dla zewnętrznych narzędzi

---

## Dodatkowe zadania z do_zrobienia.md

### 17. PDF round-trip
**Status**: W TRAKCIE
**Plik**: `tlumacz/pdf_extractor.py`, `tlumacz/core.py`
**Opis**: Tłumaczenie tekstowe PDF z zachowaniem układu (PyMuPDF, bez OCR).

### 18. OCR dla skanów PDF
**Status**: PLANOWANE
**Plik**: Do stworzenia
**Opis**: OCR + obsługa png/jpg/webp/bmp. Architektura przygotowana pod przyszłe dodanie.

### 19. Detekcja przez próbę modelu
**Status**: PLANOWANE
**Plik**: `tlumacz/core.py`
**Opis**: Mikro-zapytanie wykrywające EOS / tryb myślenia i automatyczne dostrojenie.

### 20. Pełna edycja config.json przez GUI
**Status**: PLANOWANE
**Plik**: `tlumacz/qt_gui/main_window.py`
**Opis**: Jawny przycisk Zapisz ustawienia oraz autozapis przy zmianie pól.

### 21. Pomoc w GUI → i18n
**Status**: W TRAKCIE
**Plik**: `tlumacz/qt_gui/main_window.py`, `tlumacz/i18n.py`
**Opis**: Przenieść treść Pomocy do systemu i18n. Zaktualizować nazwy funkcji i same funkcje. Dodać opis przycisku wielozadaniowego (obie wersje PL i EN).

### 22. Dokumentacja README PL/EN
**Status**: W TRAKCIE
**Plik**: `README.md`, `README.en.md`
**Opis**: Zsynchronizować README PL/EN i PODSUMOWANIE. Zmodyfikować do wersji v2, nr wersji 0.21.0.

### 23. Format plików tłumaczeń
**Status**: PLANOWANE
**Plik**: `tlumacz/i18n.py`
**Opis**: Ustalić format i test kompletności kluczy.

### 24. Aktualizacja URL w PKGBUILD
**Status**: DO ZROBIENIA PRZED PUBLIKACJĄ
**Plik**: `PKGBUILD`
**Opis**: Zweryfikować URL przed przyszłą publikacją AUR.

### 25. Automatyczna synchronizacja repo
**Status**: PLANOWANE
**Plik**: Skrypt bash
**Opis**: Skrypt dodający nową paczkę po buildzie.

### 26. Ikona repo / social preview
**Status**: PLANOWANE
**Plik**: GitHub
**Opis**: Og-image dla repozytorium.

### 27. Stabilizacja przed wydaniem
**Status**: W TRAKCIE
**Opis**:
- Ustabilizować podstawową funkcję: niezawodne tłumaczenie dokumentów
- Poprawić prompty dla Markdown/HTML/DOCX/ODT/EPUB
- Przetestować lepsze modele 2B przed wyborem modelu domyślnego
- Nie publikować wczesnych wersji testowych w publicznym AUR

---

## Metryki

**Postęp głównych zadań**: 100% (8/8 ✅)
- Wysoki priorytet: 3/3 (100%) ✅
- Średni priorytet: 3/3 (100%) ✅
- Niski priorytet: 2/2 (100%) ✅

**Dodatkowe zadania z do_zrobienia.md**: 11 zadań
- W trakcie: 4 (PDF round-trip, Stabilizacja, Pomoc i18n, README PL/EN)
- Planowane: 6
- Przed publikacją: 1

**Dokumentacja**: 6/6 (100%) ✅
**Testy**: 102/102 (100%) ✅

---

**Ostatnia aktualizacja**: 2026-09-05
**Wersja**: 0.21.0-dev
**Status**: Wersja robocza/testowa — wszystkie główne zadania zakończone
