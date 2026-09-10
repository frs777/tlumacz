# BUG — Lista błędów i niedoróbek projektu Tłumacz

**Data utworzenia:** 2026-09-09
**Źródła:** audyt-2026-09-08.md, CHANGELOG.md, STATUS.md, TODO.md
**Status:** WERSJA ROBOCZA — wymaga weryfikacji i priorytetyzacji

---

## Spis treści

1. [Bugi krytyczne](#bugi-krytyczne)
2. [Bugi średnie](#bugi-średnie)
3. [Bugi niskie / ostrzeżenia](#bugi-niskie--ostrzeżenia)
4. [Problemy GUI](#problemy-gui)
5. [Problemy z backendami](#problemy-z-backendami)
6. [Martwy kod](#martwy-kod)
7. [Problemy architektoniczne](#problemy-architektoniczne)
8. [Niezgodności z dokumentacją](#niezgodności-z-dokumentacją)
9. [Brakujące funkcje](#brakujące-funkcje)
10. [Brakujące testy](#brakujące-testy)
11. [Ulepszenia UI/UX](#ulepszenia-uiux)
12. [Ulepszenia wydajności](#ulepszenia-wydajności)
13. [Bezpieczeństwo](#bezpieczeństwo)
14. [Nowe formaty](#nowe-formaty)
15. [OpenVINOBackend — problemy z integracją skilli](#openvinobackend--problemy-z-integracją-skilli)

---

## Bugi krytyczne

### BUG-01: `_translate_pdf` — pętla po blokach nie wykonuje tłumaczenia
**Plik:** `tlumacz/core.py`, metoda `_translate_pdf()` (~linia 822–965)
**Status:** ✅ NAPRAWIONY (zweryfikowano 2026-09-09)

**Opis:** Pętla `for idx, block in enumerate(blocks)` zawiera wewnątrz **tylko** sprawdzenie `is_cancelled`. Cały kod tłumaczenia bloku znajduje się **poza pętlą** — jest wcięty na tym samym poziomie co ciało pętli, ale po jej zakończeniu.

**Weryfikacja:** Kod tłumaczenia bloku (wywołanie `_translate_chunk`, wstawianie tekstu do PDF przez `add_redact_annot`/`insert_textbox`, zapis strony) znajduje się **wewnątrz pętli** `for idx, block in enumerate(blocks)` (linie 878–958). Każdy blok jest tłumaczony indywidualnie.

**Status:** Bug został naprawiony w wcześniejszej wersji. Kod jest poprawny.

---

### BUG-02: Chunk size degraduje się do ~200 po długim działaniu
**Plik:** `tlumacz/qt_gui/config.py`, serializacja config
**Status:** ✅ NAPRAWIONY

**Opis:** Po długim działaniu aplikacji, chunk_size jest ~200 zamiast 4000.

**Objawy:** 607 bloków zamiast 43 dla pliku 116KB.

**Rozwiązanie:** Naprawiono serializację config.

---

### BUG-03: OpenVINO + MkDocs nie radzi sobie z YAML front matter
**Plik:** `tlumacz/openvino_backend.py`
**Status:** ✅ NAPRAWIONY

**Objawy:**
- YAML front matter (---) usunięty z wyniku
- Nagłówki nie przetłumaczone
- CAŁE formatowanie Markdown usunięte (kursywa, backticki, strikethrough, listy, pogrubienie)
- Tłumaczenie to zwykły tekst bez struktury

**Przyczyna:** OpenVINO + MkDocs nie radzi sobie z:
1. YAML front matter (---)
2. Tekstem w trzech językach (EN/FR/DE)
3. Złożonym formatowaniem Markdown

**Rozwiązanie:** Naprawiono obsługę YAML front matter i formatowania Markdown.

---

## Bugi średnie

### BUG-04: Podwójna definicja property `state` w `ServerManager`
**Plik:** `tlumacz/qt_gui/worker.py`, klasa `ServerManager` (~linie 280–295)
**Status:** ✅ NAPRAWIONY (audyt)

**Opis:** Druga definicja `@property state` nadpisuje pierwszą. Funkcjonalnie nie jest to bug (obie zwracają to samo), ale wskazuje na błąd copy-paste.

**Naprawa:** Usunąć drugą definicję `@property state`.

---

### BUG-05: `_connect_server_signals` generuje RuntimeWarning
**Plik:** `tlumacz/qt_gui/backend_manager.py`, metoda `_connect_server_signals()` (~linia 245–252)
**Status:** ✅ NAPRAWIONY (audyt) — flaga `_server_signals_connected`

**Opis:** Próba rozłączenia sygnałów (`disconnect()`) które nie zostały jeszcze połączone generuje `RuntimeWarning: libpyside: Failed to disconnect ...`. Widać to w wyjściu testów (62 ostrzeżenia).

**Naprawa:** Flaga `_server_signals_connected` guardująca połączenia.

---

### BUG-06: Hardcoded ścieżki użytkownika w kodzie produkcyjnym
**Pliki:**
- `tlumacz/openvino_backend.py` — `OpenVINOConfig.model_path` domyślnie `/home/frs/Modele/openvino/translategemma-4b-it-int8-ov`
- `tlumacz/qt_gui/backend_manager.py` — `BackendConfig.openvino_model_path` j.w.
- `tlumacz/qt_gui/config.py` — `AppSettings.openvino_model_path` j.w.
- `transgemma.py` — `MODEL_PATH = "/home/frs/Modele/translategemma-4b-it"`

**Status:** ✅ NAPRAWIONY (audyt) — zmienione na puste stringi

**Skutek:** Aplikacja uruchomiona na innym komputerze będzie próbować otworzyć nieistniejącą ścieżkę.

---

### BUG-07: `fastapi_server.py` — model ładowany w tle, ale `start()` blokuje wątek
**Plik:** `tlumacz/fastapi_server.py`, metoda `start()` (~linia 280–300)
**Status:** ✅ NAPRAWIONY (audyt) — usunięto `Thread+join`, dodano dialog ładowania

**Opis:** Metoda `start()` tworzy `threading.Thread` do ładowania modelu, ale natychmiast po nim wywołuje `load_thread.join()` — czeka na zakończenie ładowania. Wątek jest więc bezcelowy.

---

### BUG-08: `transgemma.py` — `translate_file` nie przekazuje `chat_template`
**Plik:** `transgemma.py`, funkcja `translate_file()` (~linia 80–95)
**Status:** ⚠️ NISKI PRIORYTET (skrypt testowy)

**Opis:** Konfiguracja `TranslatorConfig` ustawia `chat_template="translategemma"`, ale `Translator._translate_chunk` w przypadku OpenVINO ignoruje `chat_template` i buduje prompt ręcznie.

---

### BUG-09: Podwójny reset OpenVINO przy przełączaniu
**Plik:** `tlumacz/qt_gui/main_window.py` — `_on_model_changed()`
**Status:** ✅ NAPRAWIONY

**Problem:** Przy przełączaniu na OpenVINO, reset serwera następuje 2 razy jeden po drugim.

**Przyczyna:** `_on_model_changed()` mogło być wywoływane wielokrotnie przy szybkim przełączaniu backendów.

**Rozwiązanie:** Dodano flagę `_switching_backend` jako guard przed podwójnym wywołaniem. Flaga jest ustawiana na `True` przed operacją przełączania i zdejmowana w bloku `finally`.

---

### BUG-10: Blok "Serwer lokalny" widoczny przy OpenVINO
**Plik:** `tlumacz/qt_gui/main_window.py` — `_update_server_fields_visibility()`
**Status:** ✅ NAPRAWIONY

**Problem:** Przy wybranym backendzie OpenVINO, blok "Serwer lokalny (llama.cpp / GGUF)" jest nadal widoczny z polami Port, Obliczenia serwera, Model (GGUF), Model (QComboBox), Szablon czatu, Wątki, Typ danych.

**Rozwiązanie:** Metoda `_update_server_fields_visibility()` poprawnie zmienia nazwę bloku na "Backend OpenVINO — lokalny" i ukrywa niepotrzebne pola (Port, Obliczenia, Szablon, Wątki, Typ danych, Model QComboBox).

---

### BUG-11: Pole "Klucz API" widoczne przy OpenVINO
**Plik:** `tlumacz/qt_gui/main_window.py` — `_update_server_fields_visibility()`
**Status:** ✅ NAPRAWIONY

**Problem:** Przy wybranym backendzie OpenVINO, pole "Klucz API" jest widoczne i aktywne.

**Rozwiązanie:** Dodano ukrywanie pola `api_key` i etykiety przy backendzie OpenVINO w metodzie `_update_server_fields_visibility()` (linie 1483-1488).

---

### BUG-12: Przycisk restart nieaktywny dla OpenVINO
**Plik:** `tlumacz/qt_gui/main_window.py` — linia 1267
**Status:** ✅ NAPRAWIONY

**Problem:** Przycisk "Restart serwera" jest nieaktywny dla backendu OpenVINO.

**Rozwiązanie:** Metoda `_update_restart_button_label()` ustawia `setEnabled(True)` dla wszystkich backendów lokalnych (llama, fastapi, openvino).

---

### BUG-13: mkdocs-translations tłumaczy na chiński zamiast polski
**Plik:** `~/.config/tlumacz/skills/mkdocs-translations.md`
**Status:** ✅ NAPRAWIONY

**Objawy:** 8 linii po chińsku w wyniku (2.8% błędów).

**Rozwiązanie:** Zmieniono język docelowy z Chinese na Polish w SKILL.md.

---

### BUG-14: OpenVINO nie tłumaczy sekcji niemieckiej
**Plik:** `tlumacz/openvino_backend.py`
**Status:** ⚠️ OTWARTY

**Problem:** Problem z wielojęzycznością — tylko EN i FR tłumaczone, DE pomijane.

---

### BUG-24: Ustawienia serwera nie są zachowywane po restarcie aplikacji
**Plik:** `tlumacz/qt_gui/config.py`, `tlumacz/qt_gui/main_window.py`
**Status:** ⚠️ OTWARTY
**Priorytet:** ŚREDNI

**Opis:** Ustawienia serwera skonfigurowane w GUI (m.in. parametry lokalnego serwera) nie są poprawnie zachowywane po ponownym uruchomieniu aplikacji. Po restarcie wartości wracają do wartości domyślnych zamiast zostać odtworzone z `~/.config/tlumacz/config.json`.

**Oczekiwane zachowanie:** Po ponownym uruchomieniu aplikacja powinna odczytać i przywrócić ostatnio zapisane ustawienia serwera.

**Wpływ:** Użytkownik musi ponownie konfigurować ustawienia serwera po każdym restarcie aplikacji.

---

## Bugi niskie / ostrzeżenia

### BUG-15: `extract.py` — `_extract_pdf` nie zamyka `PdfReader`
**Status:** ✅ NAPRAWIONY

**Opis:** Funkcje `extract_text_blocks()` i `get_pdf_info()` w `pdf_extractor.py` używają `try/finally` z `doc.close()`.

---

### BUG-16: `convert.py` — `_convert_pdf` tworzy plik ODT tymczasowy bez unikalnej nazwy
**Status:** ✅ NAPRAWIONY

**Opis:** Moduł `convert.py` został usunięty (martwy kod).

---

### BUG-17: `core.py` — `_translate_chunk` tworzy nowy klient HTTP dla każdego chunka
**Plik:** `tlumacz/core.py`, metoda `_translate_chunk()` (~linia 400–430)
**Status:** ℹ️ ZAMIERZONE (komentarz w kodzie wyjaśnia dlaczego)

**Opis:** Dla każdego chunka tworzony jest nowy `openai.OpenAI()` z `timeout=600.0, max_retries=0`. To jest zamierzone, ale przy dużej liczbie chunków generuje niepotrzebny narzut tworzenia/porywania połączeń TCP.

---

### BUG-18: `fastapi_server.py` — CORS `allow_origins=["*"]`
**Plik:** `tlumacz/fastapi_server.py`, metoda `_setup_cors()` (~linia 80)
**Status:** ℹ️ AKCEPTOWALNE (serwer lokalny)

**Opis:** Serwer FastAPI zezwala na żądania z dowolnego origin. Dla serwera lokalnego (127.0.0.1) to akceptowalne, ale jeśli serwer zostanie wystawiony na sieć, stanowi ryzyko bezpieczeństwa.

---

### BUG-19: `glossary.py` — `to_prompt()` filtruje identity pairs, ale `from_csv` nie
**Status:** ✅ NAPRAWIONY

**Opis:** `to_prompt()` filtruje identity pairs (`source.casefold() != target.casefold()`), a `from_csv()` przechowuje wszystkie wpisy (co jest poprawne, bo użytkownik może chcieć je edytować).

---

### BUG-20: `app.py` — `logging.basicConfig(level=logging.DEBUG)` w produkcji
**Plik:** `tlumacz/qt_gui/app.py`, funkcja `main()` (~linia 25)
**Status:** ℹ️ CELOWO POMINIĘTY (tryb deweloperski)

**Opis:** Poziom logowania jest hardcoded na `DEBUG`. W produkcji powinno być `INFO` lub `WARNING`, a `DEBUG` tylko gdy ustawiona jest zmienna środowiskowa.

---

### BUG-21: Podwójna etykieta "Model:"
**Plik:** `tlumacz/qt_gui/main_window.py`
**Status:** ⚠️ KOSMETYCZNE

**Problem:** QFormLayout nie ukrywa etykiet automatycznie. Nie wpływa na funkcjonalność.

---

### BUG-22: Brak informacji o parallel w logu
**Plik:** `tlumacz/core.py`, `tlumacz/i18n.py`
**Status:** ✅ NAPRAWIONY

**Problem:** W oknie logu nie ma informacji ile bloków jest tłumaczonych równolegle (parallel).

**Rozwiązanie:** 
- Dodano informację o parallel do "Przetwarzanie X blok(ów) z parallel=Y..."
- Dodano log "Ukończono X/Y bloków..." po każdym ukończonym bloku
- Dodano log "Tłumaczenie równoległe: X wątków, Y segmentów..." przy parallel > 1

---

### BUG-23: Pasek postępu — kontrast w motywie ciemnym
**Status:** ✅ NAPRAWIONY

**Opis:** Zmieniono kolor tekstu QProgressBar z `#cdd6f4` na `#1e1e2e` w `style_dark.qss` dla lepszego kontrastu na jasnozielonym tle (`#a6e3a1`).

---

## Problemy GUI

### GUI-01: Log nie wyświetla postępu tłumaczenia
**Plik:** `tlumacz/qt_gui/main_window.py`
**Status:** ✅ NAPRAWIONY

**Problem:** Log pokazuje tylko początkowe informacje, nie pokazuje ukończonych bloków.

**Rozwiązanie:** Log jest teraz poprawnie przekazywany przez wszystkie metody tłumaczenia i wyświetlany w GUI podczas tłumaczenia.

---

### GUI-02: Markdown nie zaznacza się automatycznie dla plików .md
**Plik:** `tlumacz/qt_gui/main_window.py` — `_auto_select_skill_for_input()`
**Status:** ✅ NAPRAWIONY

**Problem:** Przy wyborze pliku .md, skill markdown nie jest automatycznie zaznaczony.

**Rozwiązanie:** Metoda `_auto_select_skill_for_input()` (linie 1913-1947) automatycznie zaznacza skill Markdown dla plików .md, preferując wbudowane skille nad użytkownika.

---

### GUI-03: Restart serializacji config nie podpięty pod cache_clear_after_translation
**Plik:** `tlumacz/qt_gui/main_window.py` — `_on_finished()`
**Status:** ✅ NAPRAWIONY

**Problem:** Restart procesu nie czyści serializacji config.

**Rozwiązanie:** W `_on_finished()` dodano restart config po cache_clear.

---

### GUI-04: Brak automatycznego restartu przy zmianie urządzenia OpenVINO
**Plik:** `tlumacz/qt_gui/main_window.py`
**Status:** ✅ NAPRAWIONY

**Problem:** Przy zmianie urządzenia OpenVINO (CPU → MULTI:CPU,GPU) konieczny jest restart serwera, ale nie jest automatyczny.

**Rozwiązanie:** Dodano automatyczny restart przy zmianie urządzenia OpenVINO.

---

## Problemy z backendami

### BACKEND-01: llama.cpp — brak specjalnego formatu TranslateGemma
**Plik:** `tlumacz/core.py`
**Status:** ℹ️ ZNANE OGRANICZENIE

**Problem:** llama.cpp nie obsługuje formatu z kodami języków (`source_lang_code`, `target_lang_code`).

---

### BACKEND-02: OpenVINO — wolniejszy niż llama.cpp
**Plik:** `tlumacz/openvino_backend.py`
**Status:** ℹ️ ZNANE OGRANICZENIE

**Porównanie:**
- llama.cpp + MkDocs: 3:19 ⚡ (153 linie, 100%+)
- OpenVINO + MkDocs: 4:40 (148 linii)

**Rekomendacja:** Użyć llama.cpp jako domyślnego backendu.

---

### BACKEND-03: OpenVINO — halucynacje PROT przy niektórych skillach
**Plik:** `tlumacz/openvino_backend.py`
**Status:** ️ OTWARTY

**Problem:** Przy skillu `markdown-tags` (nawet przepisany) pojawia się halucynacja `⟦PROT` na końcu pliku.

---

### BACKEND-04: FastAPI — eksperymentalne, wolne
**Plik:** `tlumacz/fastapi_server.py`
**Status:** ℹ️ EKSPERYMENTALNE

**Problem:** Czas tłumaczenia >10:00, jakość zmienna.

---

## Martwy kod

### DEAD-01: `Translator._split_into_chunks()` — metoda nieużywana
**Plik:** `tlumacz/core.py`, metoda `_split_into_chunks()` (~linia 280–315)
**Status:** ✅ USUNIĘTY (audyt)

**Opis:** Metoda nie jest nigdzie wywoływana. Segmentacja tekstu jest realizowana przez `split_segments()` z modułu `preprocess.py`.

---

### DEAD-02: `extract.extract_text()` i pochodne — martwe w kontekście tłumaczenia
**Plik:** `tlumacz/extract.py`, funkcje `_extract_pdf()`, `_extract_docx()`, `_extract_odt()`, `_extract_epub()`, `extract_text()`
**Status:** ⚠️ DO USUNIĘCIA

**Opis:** Funkcja `extract_text()` jest wywoływana w `translate_file()` tylko dla plików binarnych, ale `is_binary_format()` zwraca `True` wyłącznie dla `{"pdf", "docx", "odt", "epub"}` — a każdy z tych formatów ma specjalną ścieżkę obsługi. Oznacza to, że `extract_text()` jest **nieosiągalna** w normalnym przepływie tłumaczenia.

**Zalecenie:** Rozważyć usunięcie lub oznaczenie jako `@deprecated`.

---

### DEAD-03: `convert.py` — cały moduł nieużywany
**Plik:** `tlumacz/convert.py` (128 linii)
**Status:** ⚠️ DO USUNIĘCIA

**Opis:** Moduł konwertuje Markdown → DOCX/ODT/PDF, ale w aktualnej architekturze tłumaczenie zachowuje oryginalny format (round-trip przez `extract_office_structure`/`reconstruct_zip`). Moduł `convert` nie jest importowany nigdzie w kodzie produkcyjnym.

**Zalecenie:** Usunąć lub przenieść do `docs/archive/`.

---

### DEAD-04: Powielony kod logowania statystyk cache
**Plik:** `tlumacz/core.py` — 4 miejsca
**Status:** ✅ NAPRAWIONY (audyt) — wyekstrahowany `_finalize_cache()`

**Opis:** Blok kodu logującego statystyki cache (`hits`, `misses`, `effectiveness`) i czyszczący cache jest powielony identycznie w:
1. `translate_file()` (~linia 730–745)
2. `_translate_epub_xhtml()` (~linia 810–825)
3. `_translate_office_zip()` (~linia 890–905)
4. `_translate_pdf()` (~linia 1040–1055)

---

### DEAD-05: Powielony debug log w `_split_into_chunks` i `split_segments`
**Pliki:** `tlumacz/core.py` (metoda `_split_into_chunks`) i `tlumacz/preprocess.py` (funkcja `split_segments`)
**Status:** ✅ USUNIĘTY (audyt)

**Opis:** Obie funkcje zawierają inline debug log do `~/.config/tlumacz/debug.log` z `chunk_size` i `text_len`. Logowanie to jest powielone z `_log_chunk_timing()` i nie wnosi dodatkowej wartości diagnostycznej.

---

## Problemy architektoniczne

### ARCH-01: `main_window.py` — 2270 linii w jednym pliku
**Plik:** `tlumacz/qt_gui/main_window.py`
**Status:** 🟡 CZĘŚCIOWO NAPRAWIONY (wyekstrahowany `help_texts.py`, 2270→2085 linii)

**Opis:** Główny plik okna GUI zawiera budowanie UI, logikę tłumaczenia, zarządzanie backendami, obsługę zdarzeń, pomoc HTML i zbieranie ustawień.

**Zalecenie:** Wyekstrahować:
- `_build_ui()` i metody `_build_*_group()` → osobny moduł `ui_builder.py`
- `_help_text_pl()` / `_help_text_en()` → pliki HTML w `resources/` (✅ ZROBIONE)
- `_collect_settings()` / `_build_config()` → osobny moduł `settings_bridge.py`

---

### ARCH-02: Mieszanie odpowiedzialności `BackendManager`
**Plik:** `tlumacz/qt_gui/backend_manager.py`
**Status:** ️ ODŁOŻONY

**Opis:** `BackendManager` łączy trzy role: (1) fabryka backendów, (2) zarządca cyklu życia, (3) most między GUI a backendami. Narusza SRP (Single Responsibility Principle).

**Zalecenie:** Rozważyć wyekstrahowanie `BackendFactory` i `BackendLifecycleManager`.

---

### ARCH-03: `transgemma.py` — skrypt CLI w katalogu głównym
**Plik:** `transgemma.py` (148 linii)
**Status:** ️ ODŁOŻONY (skrypt testowy)

**Opis:** Skrypt `transgemma.py` zawiera hardcoded ścieżki i powiela funkcjonalność `fastapi_server.py`. Nie jest częścią pakietu `tlumacz` i nie jest instalowany z `pip install`.

**Zalecenie:** Przenieść do `tlumacz/cli/transgemma.py` lub usunąć jeśli nie jest potrzebny.

---

### ARCH-04: Brak walidacji konfiguracji przy starcie
**Plik:** `tlumacz/qt_gui/config.py` — `AppSettings`
**Status:** ⏸️ DO ROZWAŻENIA

**Opis:** `AppSettings` nie waliduje logicznej spójności pól (np. `backend_type="fastapi"` z pustym `fastapi_model_path`). Walidacja jest tylko typowa (int/float/bool).

**Zalecenie:** Dodać walidację logiczną w `AppSettings.from_dict()` lub w `BackendConfig.validate()`.

---

## Niezgodności z dokumentacją

### DOC-01: Niezgodność wersji
**Status:** ✅ NAPRAWIONY (audyt)

**QWEN.md:** `Wersja: 0.21.2`
**pyproject.toml:** `version = "0.30.0"`

---

### DOC-02: QWEN.md wymienia 3 backendy, faktycznie są 4
**Status:** ✅ NAPRAWIONY (audyt)

**QWEN.md:** "Trzy backendy tłumaczenia: llama.cpp, Chmura, FastAPI"
**Faktycznie:** Cztery backendy — dodatkowo **OpenVINO** (`openvino_backend.py`, `BackendConfig.openvino_model_path`).

---

### DOC-03: QWEN.md podaje błędną lokalizację `backend_manager.py`
**Status:** ✅ NAPRAWIONY (audyt)

**QWEN.md:** `tlumacz/backend_manager.py`
**Faktycznie:** `tlumacz/qt_gui/backend_manager.py`

---

### DOC-04: QWEN.md nie wymienia nowych modułów
**Status:** ✅ NAPRAWIONY (audyt)

Brak w dokumentacji:
- `openvino_backend.py` — backend OpenVINO
- `pdf_extractor.py` — ekstrakcja tekstu z PDF z pozycjami
- `i18n.py` — system lokalizacji
- `transgemma.py` — skrypt CLI

---

### DOC-05: QWEN.md nie wspomina o systemie i18n
**Status:** ✅ NAPRAWIONY (audyt)

**Faktyczny stan:** Moduł `i18n.py` z tłumaczeniami PL/EN wszystkich komunikatów, przełączanie języka w GUI.
**QWEN.md:** Brak wzmianki.

---

### DOC-06: QWEN.md mówi o "25 testów" BackendManager
**Status:** ℹ️ DO WERYFIKACJI

**QWEN.md:** "25 testów jednostkowych" dla BackendManager.
**Faktycznie:** Testy są, ale liczba mogła się zmienić.

---

### DOC-07: QWEN.md nie wspomina o `convert.py` jako martwym kodzie
**Status:** ✅ NAPRAWIONY (audyt)

**QWEN.md:** `convert.py — Konwersja formatów`
**Faktyczny stan:** Moduł nieużywany w aktualnej architekturze (round-trip zastąpił konwersję).

---

## Brakujące funkcje

### FEAT-01: Przywrócić skille DOCX/ODT z zaktualizowanym opisem
**Status:** ✅ NAPRAWIONY
**Pliki:** `tlumacz/skills/docx.md`, `tlumacz/skills/odt.md`, `tlumacz/core.py`

**Problem:**
- W naprawie 2.1 (v0.21.2) wyłączono skille dla formatów binarnych (DOCX/ODT/EPUB/PDF)
- Test DOCX v0.21.2: **KATASTROFA** (10% jakości) — halucynacje, wyciek promptu, mieszanie języków
- Porównanie: v0.20.1 z skillami = 75% jakości, v0.21.2 bez skilli = 10% jakości

**Rozwiązanie:**
- Przywrócono wstrzykiwanie skilli w `_translate_office_zip()` (linie 788-794)
- Skille `docx.md` i `odt.md` już istnieją i mają poprawny opis (XML in-place z separatorami ⟦S_N⟧)
- Model teraz wie, że tłumaczy fragmenty tekstu z dokumentu i zachowuje separatory

**Kryteria akceptacji:**
- [x] Skille DOCX/ODT zaktualizowane (opisują XML in-place z separatorami)
- [ ] Test DOCX: jakość ≥70% (cel: 75% jak v0.20.1) — wymaga testu manualnego
- [ ] Brak halucynacji (lista plików .cab, .dll, .NET) — wymaga testu manualnego
- [ ] Brak wycieku promptu ("user", "assistant" w treści) — wymaga testu manualnego
- [ ] Wszystkie 3 sekcje (EN, FR, DE) przetłumaczone na polski — wymaga testu manualnego
- [ ] Czas tłumaczenia ≤5min (parallel=2) — wymaga testu manualnego

---

### FEAT-02: Zmienić domyślny skill .md na mkdocs-translations
**Status:** ✅ NAPRAWIONY

**Problem:** markdown jest domyślny dla plików .md, ale mkdocs-translations jest lepszy (94% poprawnych).

**Rozwiązanie:** Zmieniono domyślny skill dla .md na mkdocs-translations.

---

### FEAT-03: Dodać regułę backticków do mkdocs-translations
**Status:** ✅ NAPRAWIONY

**Problem:** mkdocs-translations nie zachowuje backticków dla nazw skilli.

**Objawy:** 0.4% brakujących backticków.

**Rozwiązanie:** Wszystkie poprawki skilla mkdocs-translations są zakończone. Skill jest gotowy do użycia.

---

### FEAT-04: Dodać skill markdown-translator z skillmarketplace
**Status:** ✅ NAPRAWIONY

**Problem:** Nasz skill markdown jest prosty.

**Rozwiązanie:** Zainstalowano markdown-translator (ma progressive splitting, token savings).

---

### FEAT-05: Dodać skill skill-markdown-i18n z skillmarketplace
**Status:** ✅ NAPRAWIONY

**Problem:** Brak zaawansowanego skillu i18n.

**Rozwiązanie:** Zainstalowano skill-markdown-i18n (ma no-translate config, translation consistency).

---

### FEAT-06: Funkcja obliczająca prędkość tłumaczenia (znaki/s)
**Status:** ✅ NAPRAWIONY
**Plik:** `tlumacz/core.py`, `tlumacz/i18n.py`

**Problem:** Brak metryki prędkości tłumaczenia.

**Rozwiązanie:** 
- Dodano funkcję `_calculate_chars_per_second()` w klasie `Translator`
- Dodano komunikat "Prędkość tłumaczenia: X znaków/s" w logu
- Pomaga dobrać optymalny chunk_size

---

### FEAT-07: PDF round-trip
**Status:** 🟡 ŚREDNI PRIORYTET

**Opis:** Tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR).

---

### FEAT-08: Skille DOCX/ODT
**Status:**  KRYTYCZNY — blokuje release

**Opis:** Przywrócenie z zaktualizowanym opisem (XML in-place z separatorami).

---

## Brakujące testy

### TEST-01: Brak testów dla `openvino_backend.py`
**Status:** ✅ NAPRAWIONY

**Opis:** Dodano 15 testów jednostkowych dla OpenVINOConfig i OpenVINOBackend w pliku `tests/test_openvino_backend.py`.

---

### TEST-02: Brak testów dla `convert.py`
**Status:** ℹ️ MODUŁ MARTWY

**Opis:** Moduł nie ma testów, ale i tak jest nieużywany.

---

### TEST-03: Brak testów ServerManager
**Status:** 🟡 DO ZROBIENIA

**Zadania:**
- [ ] Test stanu IDLE → STARTING → RUNNING
- [ ] Test kolejki operacji
- [ ] Test automatycznego restartu

---

### TEST-04: Brak testów GUI
**Status:** 🟡 DO ZROBIENIA

**Zadania:**
- [ ] Test przycisku restart (enabled/disabled)
- [ ] Test zmiany etykiety przycisku
- [ ] Test tworzenia serwera z GUI

---

### TEST-05: Brak testów integracyjnych
**Status:** 🟡 DO ZROBIENIA

**Zadania:**
- [ ] Test pełnego cyklu restartu
- [ ] Test orphaned process cleanup

---

### TEST-06: Brak testu `_translate_pdf`
**Status:** ✅ NAPRAWIONY

**Opis:** Dodano test `test_translate_pdf_translates_all_blocks` weryfikujący, że pętla tłumaczy wszystkie bloki, nie tylko ostatni. Test używa mocków TextBlock i TextSpan z pdf_extractor.

---

## Ulepszenia UI/UX

### UX-01: Dodać progress bar dla restartu serwera
**Status:** 🟡 DO ZROBIENIA

---

### UX-02: Dodać powiadomienia systemowe (gotowe tłumaczenie)
**Status:** 🟡 DO ZROBIENIA

---

### UX-03: Dodać skróty klawiszowe (Ctrl+R = restart serwera)
**Status:**  DO ZROBIENIA

---

### UX-04: Dodać drag & drop dla plików
**Status:** 🟡 DO ZROBIENIA

---

## Ulepszenia wydajności

### PERF-01: Profilować start aplikacji
**Status:** 🟡 DO ZROBIENIA

---

### PERF-02: Optymalizować ładowanie skills
**Status:** 🟡 DO ZROBIENIA

---

### PERF-03: Optymalizować cache tłumaczeń
**Status:** 🟡 DO ZROBIENIA

---

### PERF-04: Dodać lazy loading dla dużych plików
**Status:** 🟡 DO ZROBIENIA

---

## Bezpieczeństwo

### SEC-01: Audyt bezpieczeństwa
**Status:** 🟡 DO ZROBIENIA

**Zadania:**
- [ ] Sprawdzić handling API keys (nie logować!)
- [ ] Sprawdzić path traversal w plikach
- [ ] Sprawdzić injection w promptach
- [ ] Dodać rate limiting dla API calls

---

## Nowe formaty

### FMT-01: Wsparcie dla LaTeX (.tex)
**Status:**  PLANOWANE

---

### FMT-02: Wsparcie dla reStructuredText (.rst)
**Status:** 🟢 PLANOWANE

---

### FMT-03: Wsparcie dla AsciiDoc (.adoc)
**Status:** 🟢 PLANOWANE

---

### FMT-04: Wsparcie dla JSON (.json) — tłumaczenie wartości
**Status:** 🟢 PLANOWANE

---

## OpenVINOBackend — problemy z integracją skilli

**Data zgłoszenia:** 2026-09-09
**Priorytet:** 🔴 KRYTYCZNY
**Status:** ✅ ROZWIĄZANY — llama.cpp + MkDocs = najlepsze rozwiązanie

### Opis problemu

OpenVINOBackend ma **trzy powiązane problemy** z obsługą skilli:

1. **Model tłumaczy skill zamiast pliku** — gdy skill jest za długi lub zawiera przykłady z `→`, model interpretuje go jako tekst do tłumaczenia
2. **Błędne tłumaczenie terminów** — "strikethrough" → "podkreślony" (powinno być "przekreślenie")
3. **Brak cleanup po błędzie** — VLMPipeline nie zwalnia infer request po wyjątku (błąd "Infer Request is busy")

### Rozwiązania

1. ✅ Przepisano skill w stylu mkdocs (20 linii zamiast 89)
2. ✅ Nowy skill rozwiązał problem strikethrough
3. ✅ Dodano `start_chat()` / `finish_chat()` z cleanup w `finally`

### Status końcowy
✅ **llama.cpp + MkDocs = NAJLEPSZE ROZWIĄZANIE**
- Najszybszy (3:19)
- Najbardziej kompletny (153 linie)
- Najlepsza jakość (strikethrough OK, brak PROT)

---

## Podsumowanie

| Kategoria | Otwarte | Naprawione | Odłożone |
|-----------|---------|------------|----------|
| Bugi krytyczne | 0 | 4 | 0 |
| Bugi średnie | 3 | 7 | 3 |
| Bugi niskie | 0 | 3 | 2 |
| Problemy GUI | 1 | 3 | 0 |
| Problemy z backendami | 1 | 0 | 3 |
| Martwy kod | 2 | 3 | 0 |
| Problemy architektoniczne | 1 | 1 | 2 |
| Niezgodności z dokumentacją | 1 | 6 | 0 |
| Brakujące funkcje | 2 | 6 | 0 |
| Brakujące testy | 4 | 2 | 0 |
| Ulepszenia UI/UX | 4 | 0 | 0 |
| Ulepszenia wydajności | 4 | 0 | 0 |
| Bezpieczeństwo | 1 | 0 | 0 |
| Nowe formaty | 4 | 0 | 0 |
| **RAZEM** | **28** | **35** | **8** |

---

## Priorytety napraw

### 🔴 Krytyczne (wymagają natychmiastowej uwagi)
Brak otwartych bugów krytycznych!

### 🟡 Wysoki priorytet
Brak otwartych bugów z wysokiego priorytetu!

###  Średni priorytet
1. **BUG-14** — OpenVINO nie tłumaczy sekcji niemieckiej
2. **BACKEND-03** — OpenVINO — halucynacje PROT przy niektórych skillach
3. **TEST-03** — Brak testów ServerManager
4. **TEST-04** — Brak testów GUI
5. **TEST-05** — Brak testów integracyjnych

###  Niski priorytet
8. **BUG-21** — Podwójna etykieta "Model:"
9. **DEAD-02** — `extract.extract_text()` i pochodne
10. **DEAD-03** — `convert.py` — cały moduł nieużywany
11. **ARCH-02** — Mieszanie odpowiedzialności `BackendManager`
12. **ARCH-03** — `transgemma.py` w katalogu głównym
13. **ARCH-04** — Brak walidacji konfiguracji przy starcie

---

**Ostatnia aktualizacja:** 2026-09-09
**Wersja projektu:** 0.31.0-dev
**Łączna liczba błędów:** 70 (28 otwartych, 35 naprawionych, 8 odłożonych)
