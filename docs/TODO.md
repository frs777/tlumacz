
### Zrealizowane w 0.31.1
- **O programie w zakładce Pomoc** — dodano przycisk i wyskakujące okno z wersją oraz podstawowymi informacjami.
- **Aktualizacja wersji GUI** — numer jest centralnie definiowany w `tlumacz/version.py`.

# TODO - Agent Translator V3

**Ostatnia aktualizacja:** 2026-09-09 (dodano zadania z testów skilli i błędy GUI OpenVINO)

---

## ✅ Zakończone — Testy backendów i naprawa bugów OpenVINO (2026-09-09)

### Testy porównawcze: llama.cpp vs OpenVINO vs FastAPI
**Status**: ZAKOŃCZONE
**Pliki testowe**: `pliki testowe/tagi.md`, `pliki testowe/test_2000_chars.txt`

**Wyniki testów** (plik `tagi.md`, skill MkDocs):

| Backend | Czas | Linii | Strikethrough | Halucynacje | Werdykt |
|---------|------|-------|---------------|-------------|---------|
| **llama.cpp** | **3:19** ⚡ | **153** (100%+) | ✅ przekreślony | ✅ Brak | **🏆 NAJLEPSZY** |
| OpenVINO | 4:40 | 148 | ❌ podkreślony | ✅ Brak | ⚠️ Wolniejszy |
| OpenVINO | 4:46 | 150 | ✅ przekreślony | ❌ PROT | ⚠️ Halucynacje |
| FastAPI | >10:00 | ⚠️ Zmienna | ⚠️ Zależy | ⚠️ Zależy | Eksperymentalne |

**Rekomendacja**: llama.cpp + MkDocs = najlepsze rozwiązanie (30% szybszy, najlepsza jakość)

### Naprawione bugi OpenVINO

| # | Problem | Naprawa | Plik |
|---|---------|---------|------|
| 1 | Brak cleanup po błędzie (Infer Request is busy) | Dodano `start_chat()` / `finish_chat()` z `finally` block | `openvino_backend.py` |
| 2 | Skill za długi — model tłumaczy skill zamiast pliku | Przepisano `markdown-tags.md` w stylu mkdocs (20 linii) | `~/.config/tlumacz/skills/markdown-tags.md` |
| 3 | Strikethrough → podkreślenie | Poprawione przez glosariusz + nowy skill | `openvino_backend.py` |

**Raport bugów**: `docs/BUG_OPENVINO_SKILL_INTEGRATION.md`

### Zaktualizowana dokumentacja
- ✅ `QWEN.md` — dodano sekcję "Wyniki testów backendów"
- ✅ `README_pl.md` — zaktualizowano sekcję "Cztery backendy tłumaczenia"
- ✅ `docs/STATUS.md` — dodano wyniki testów i status OpenVINO
- ✅ `docs/BUG_OPENVINO_SKILL_INTEGRATION.md` — pełny raport bugów i napraw

---

## ✅ Zakończone — Naprawy GUI (2026-09-08)

### 23 bugi GUI naprawione
**Status**: ZAKOŃCZONE
**Pliki**: `tlumacz/qt_gui/main_window.py`, `tlumacz/qt_gui/backend_manager.py`, `tlumacz/qt_gui/worker.py`, `tlumacz/qt_gui/config.py`, `tlumacz/skill.py`

**Naprawione błędy:**

| # | Problem | Naprawa |
|---|---------|---------|
| 1 | Typ serwera "local" po starcie | Ustawiany na ostatnio używany backend |
| 2 | Pola wszystkich backendów widoczne | `_update_server_fields_visibility` w `_load_settings_into_ui` |
| 3 | Brak checkboxa "Restart po tłumaczeniu" | Dodany checkbox + zapis/odczyt z config |
| 4 | Skill Markdown nie ustawia się dla .md | Preferuj wbudowane skille nad użytkownika |
| 5 | Port FastAPI nie skorelowany z URL | Aktualizacja pola Port przy zmianie backendu |
| 6 | Oba przyciski "Przeglądaj" otwierają okno wczytywania | Dialog zapisu z sugerowaną nazwą pliku |
| 7 | FastAPI/llama nie trzyma ścieżki | `_collect_settings` zachowuje pola z `self._settings` |
| 8 | "Brak konfiguracji serwera" | `_build_config_updates` zwraca ustawienia dla wybranego backendu |
| 9 | Restart nie przekazywał config | `BackendManager.restart()` przekazuje `config_updates` |
| 10 | Serwer nie restartuje przy przełączaniu | Zawsze restartuj przy przełączaniu backendu |
| 11 | Wolny restart (stop wszystkich) | Zatrzymuj tylko aktywny backend |
| 12 | Logi "Serwer lokalny" | Logi z nazwą backendu (llama.cpp/FastAPI/OpenVINO) |
| 13 | FastAPI nie startuje (worker deleteLater) | `worker.deleteLater()` po zakończeniu thread |
| 14 | Podwójne uruchomienie OpenVINO | Zapamiętaj `old_backend` przed aktualizacją |
| 15 | RuntimeError thread already deleted | Bezpieczne sprawdzenie `isRunning()` z try/except |
| 16 | Logi pokazują zły backend | Używaj `base_url` do identyfikacji backendu |
| 17 | Restart uruchamia zły backend | Przekazuj `backend` do `BackendManager.restart()` |
| 18 | Przycisk restart szary po operacji | Emituj `operation_finished` dla FastAPI/OpenVINO |
| 19 | llama.cpp nie trzyma `parallel` | `parallel: settings.server_parallel` (nie hardcoded 1) |
| 20 | FastAPI restart blokuje GUI | Użyj `_start_fastapi()` w QThread |
| 21 | FastAPI restart nie zatrzymuje | Zatrzymaj przed startem w `_start_fastapi()` |
| 22 | llama.cpp nie trzyma ustawień | `_collect_settings` zachowuje `server_port`, `server_parallel`, `server_compute_mode`, `server_chat_template` |
| 23 | Skill prompt-template-md nie ładowany | Dodano frontmatter (name, formats, description) |

**Dodatkowe usprawnienia:**
- Logowanie debugowe chunk_size w `_build_config`, `_translation_process_entry`, `_split_into_chunks`, `split_segments`
- Analiza projektów MinerU i skillmarketplace (markdown-translator, skill-markdown-i18n)
- Dodano zadania do TODO: progressive splitting, streaming I/O, no-translate config

**Testy:** Ręczne testy GUI — wszystkie backendy (llama.cpp, FastAPI, OpenVINO) działają poprawnie

---

## ✅ Zakończone — OpenVINO (2026-09-07)

### Backend OpenVINO — TranslateGemma 4B INT8
**Status**: ZAKOŃCZONE
**Pliki**: `tlumacz/openvino_backend.py`, `tlumacz/core.py`, `tlumacz/qt_gui/backend_manager.py`, `tlumacz/qt_gui/main_window.py`, `tlumacz/qt_gui/config.py`

**Zaimplementowane**:
- OpenVINOBackend z VLMPipeline — bezpośrednia inferencja bez HTTP
- Integracja z BackendManager (4. backend: openvino)
- GUI: QComboBox "OpenVINO (TranslateGemma INT8)" + urządzenie (CPU/GPU/AUTO/MULTI)
- Wzmocnienie prompta: parametr `context` (glosariusz + skill + system prompt)
- Fallback GPU→CPU gdy urządzenie niedostępne (np. AMD Radeon)
- Lazy init w procesie potomnym (pickle-safe dla multiprocessing.spawn)
- Naprawiony `_clean_output()` — nie ucina wieloliniowych tłumaczeń
- Naprawiony `APIConnectionError` — OpenVINO nie łączy się przez HTTP
- Autodetekcja języka źródłowego (`source_lang="auto"`)
- 192 testy PASSED, 0 FAILED — brak regresji

**Wydajność** (AMD Ryzen 7 5825U, CPU, model INT8):
- Ładowanie modelu: ~3s
- Tłumaczenie krótkie (~30 znaków): ~5s
- RAM: ~8 GB

**Ograniczenia**:
- OpenVINO GPU plugin wspiera Intel iGPU — AMD Radeon nie działa (fallback na CPU)
- Model text-only (vision stub nie działa)

---

## ✅ Zakończone w audycie v0.30.0 (2026-09-06)

### Audyt inżynierski — wszystkie błędy krytyczne naprawione
**Status:** ZAKOŃCZONE (2026-09-06)
**Dokumentacja:** `docs/PODSUMOWANIE_AUDYTU_v0.21.2.md`

**Naprawione błędy:**
- GUI: G1-G6 (6 błędów)
- Rdzeń: #2.1-#2.7 (7 błędów)
- Backend: #3.1-#3.7 (7 błędów)
- Skills: #4.1-#4.3 (3 błędy)

**Łącznie:** 23 błędy krytyczne naprawione

---

## Wysoki Priorytet 🔴

### 1. Przywrócić skille DOCX/ODT z zaktualizowanym opisem
**Status**: DO ZROBIENIA
**Pliki**: `tlumacz/skills/docx.md`, `tlumacz/skills/odt.md`, `tlumacz/core.py`
**Priorytet**: KRYTYCZNY — blokuje release v0.21.2

**Problem**:
- W naprawie 2.1 (v0.21.2) wyłączono skille dla formatów binarnych (DOCX/ODT/EPUB/PDF)
- Test DOCX v0.21.2: **KATASTROFA** (10% jakości) — halucynacje, wyciek promptu, mieszanie języków
- Porównanie: v0.20.1 z skillami = 75% jakości, v0.21.2 bez skilli = 10% jakości
- Skill dawał modelowi kontekst że tłumaczy dokument — bez niego model generuje losowy tekst

**Raport z testów**: `docs/jakosc_tlumaczenia_v0.21.2.md`

**Rozwiązanie**:
1. Przywrócić pliki `docx.md` i `odt.md` z zaktualizowanym opisem:
   - Opis: tłumaczenie XML in-place z separatorami ⟦S_N⟧
   - Instrukcje: zachowuj separatory, nie dodawaj Markdown, tłumacz tylko tekst
2. W `core.py` przywrócić wstrzykiwanie skilli dla DOCX/ODT w `_translate_office_zip()`
3. Przetestować z parallel=1 i parallel=2
4. Porównać jakość z v0.20.1 (chatml, 75%)

**Kryteria akceptacji**:
- [ ] Skille DOCX/ODT zaktualizowane (opisują XML in-place z separatorami)
- [ ] Test DOCX: jakość ≥70% (cel: 75% jak v0.20.1)
- [ ] Brak halucynacji (lista plików .cab, .dll, .NET)
- [ ] Brak wycieku promptu ("user", "assistant" w treści)
- [ ] Wszystkie 3 sekcje (EN, FR, DE) przetłumaczone na polski
- [ ] Czas tłumaczenia ≤5min (parallel=2)

---

### 2. BackendManager — obsługa 4 backendów ✅ ZAKOŃCZONE
**Status**: ZAKOŃCZONE (2026-09-07)
**Pliki**: `tlumacz/qt_gui/backend_manager.py`, `tlumacz/qt_gui/main_window.py`, `tlumacz/qt_gui/config.py`

**Zaimplementowane**:
- BackendManager (QObject) z sygnałami Qt: `backend_started`, `backend_stopped`, `backend_error`
- Cztery backendy: llama.cpp, Cloud API, FastAPI (TranslateGemma), **OpenVINO (TranslateGemma INT8)**
- QComboBox "Typ serwera" w GUI
- Dynamiczne pole "Model" (placeholder/tooltip zmienia się w zależności od backendu)
- Persystencja ścieżki modelu dla każdego backendu
- BackendManager podłączony w GUI (V3)

**Testy**: 138/138 przechodzą

---

### 3. Inteligentny Przycisk Restart Serwera ✅ ZAKOŃCZONE
**Status**: ZAKOŃCZONE
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

### 4. Crash przy Anulowaniu Tłumaczenia Lokalnego ✅ ZAKOŃCZONE
**Status**: ZAKOŃCZONE
**Plik**: `tlumacz/qt_gui/main_window.py`
**Problem**: `QThread: Destroyed while thread '' is still running` przy anulowaniu

**Przyczyna**: `_clear_finished_thread()` ustawiał `self._thread = None` zanim thread się zakończył. Thread był niszczony przez GC podczas gdy był "running".

**Rozwiązanie**: Wywołanie `thread.stop()` (cancel + quit + wait) przed usunięciem referencji.

**Testy**: Ręczne testy GUI — brak crashu przy anulowaniu

---

### 5. Wdrożenie Tłumaczenia w Chmurze ✅ ZAKOŃCZONE
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


## 🐛 Otwarte błędy i zadania z testów (2026-09-08)

> Poniższe zadania pochodzą z testów skilli i backendów z 2026-09-07/08.
> Niektóre mogą być już naprawione — wymaga weryfikacji.

---

### Zadania z testów skilli i tłumaczenia

# Rzeczy do zrobienia i poprawienia - 2026-09-08

## Bugi krytyczne:

### 1. Chunk size nie jest stosowany poprawnie
**Problem:** Po długim działaniu aplikacji, chunk_size jest ~200 zamiast 4000
**Objawy:** 607 bloków zamiast 43 dla pliku 116KB
**Rozwiązanie:** Restart aplikacji naprawia problem
**Status:** ⚠️ Wymaga naprawy serializacji config

### 2. Halucynacje w tłumaczeniu listy skilli
**Problem:** Modele generują halucynacje (PROT_X, powtarzający się tekst)
**Objawy:** 6-40% skilli to halucynacje
**Rozwiązanie:** Użyć mkdocs-translations (94% poprawnych)
**Status:** ✅ Zaakceptowane (6% brakujących jest OK)

---

## Funkcje do dodania:

### 3. Automatyczny restart procesu po tłumaczeniu
**Problem:** Chunk size degraduje się po długim działaniu
**Rozwiązanie:** Checkbox "Restart procesu po tłumaczeniu" w GUI
**Status:** 🔄 W implementacji (dodano checkbox)

### 4. Markdown jako domyślne zaznaczenie dla plików .md
**Problem:** Przy wyborze pliku .md, skill markdown nie jest automatycznie zaznaczony
**Rozwiązanie:** Auto-zaznaczenie w _on_input_changed()
**Status:** 📝 Do zrobienia

### 5. Podpiąć restart serializacji config pod cache_clear_after_translation
**Problem:** Restart procesu nie czyści serializacji config
**Rozwiązanie:** W _on_finished() dodać restart config
**Status:**  Do zrobienia

---

## Ulepszenia:

### 6. Zmienić domyślny skill .md na mkdocs-translations
**Problem:** markdown jest domyślny dla plików .md, ale mkdocs-translations jest lepszy
**Rozwiązanie:** Zmienić domyślny skill dla .md na mkdocs-translations
**Status:**  Do zrobienia

### 7. Naprawić mkdocs-translations - język polski
**Problem:** mkdocs-translations tłumaczy na chiński zamiast polski
**Objawy:** 8 linii po chińsku w wyniku (2.8% błędów)
**Rozwiązanie:** Zmienić język docelowy z Chinese na Polish w SKILL.md
**Status:** 📝 Do zrobienia

### 8. Dodać regułę backticków do mkdocs-translations
**Problem:** mkdocs-translations nie zachowuje backticków dla nazw skilli
**Objawy:** 0.4% brakujących backticków
**Rozwiązanie:** Dodać regułę "Zachowaj backticki `` dla nazw umiejętności"
**Status:** 📝 Do zrobienia

### 9. Dodać skill markdown-translator z skillmarketplace
**Problem:** Nasz skill markdown jest prosty
**Rozwiązanie:** Zainstalować markdown-translator (ma progressive splitting, token savings)
**Status:** 📝 Do zrobienia

### 10. Dodać skill skill-markdown-i18n z skillmarketplace
**Problem:** Brak zaawansowanego skillu i18n
**Rozwiązanie:** Zainstalować skill-markdown-i18n (ma no-translate config, translation consistency)
**Status:** 📝 Do zrobienia

---

## Testy:

### 9. Przetestować MkDocs na tagi.md
**Problem:** Nie wiemy jak MkDocs radzi sobie z różnymi tagami Markdown
**Rozwiązanie:** Przetestować na pliku z maksymalną liczbą tagów
**Status:**  Do zrobienia

### 10. Porównać markdown-translator z mkdocs-translations
**Problem:** Nie wiemy który skill jest lepszy
**Rozwiązanie:** Przetestować oba na tym samym pliku
**Status:** 📝 Do zrobienia

---

## Dokumentacja:

### 11. Zaktualizować README z nowymi skillami
**Problem:** README nie wspomina o mkdocs-translations
**Rozwiązanie:** Dodać sekcję o skillach
**Status:** 📝 Do zrobienia

### 12. Dodać dokumentację konfiguracji chunk_size
**Problem:** Użytkownicy nie wiedzą jak ustawić chunk_size
**Rozwiązanie:** Dodać sekcję w dokumentacji
**Status:**  Do zrobienia

---

## Priorytety:

### Wysoki priorytet (Bugi):
1. **Naprawa serializacji config** (bug #1) - chunk_size degraduje się do ~200
2. **Auto-zaznaczenie markdown dla .md** (funkcja #4)
3. **Restart serializacji config** (funkcja #5)

### Średni priorytet (Ulepszenia):
4. **Naprawić mkdocs-translations - język polski** (ulepszenie #7)
5. **Dodać regułę backticków do mkdocs-translations** (ulepszenie #8)
6. **Zmienić domyślny skill .md na mkdocs-translations** (ulepszenie #6)
7. **Zainstalować markdown-translator** (ulepszenie #9)
8. **Zainstalować skill-markdown-i18n** (ulepszenie #10)

### Niski priorytet (Testy/Dokumentacja):
9. **Test MkDocs na tagi.md** (test #11)
10. **Porównanie skilli** (test #12)
11. **Aktualizacja README** (dokumentacja #13)
12. **Dokumentacja chunk_size** (dokumentacja #14)

---

**Status:** 2/14 zrobione, 1/14 w implementacji, 11/14 do zrobienia


---

### Błędy GUI związane z OpenVINO

# TODO: Błędy GUI do naprawienia

**Data:** 2026-09-07
**Priorytet:** Średni (po zakończeniu testów OpenVINO)

---

## Błędy poważne

### 1. Podwójny reset OpenVINO
**Problem:** Przy przełączaniu na OpenVINO, reset serwera następuje 2 razy jeden po drugim.

**Przyczyna:** Prawdopodobnie `_on_model_changed()` wywołuje `stop_openvino()` + `start()` wielokrotnie.

**Plik:** `tlumacz/qt_gui/main_window.py` — `_on_model_changed()`

**Rozwiązanie:** Dodać debounce lub sprawdzić czy backend już działa przed restartem.

---

## Błędy drobne

### 2. Blok "Serwer lokalny (llama.cpp / GGUF)" widoczny przy OpenVINO
**Problem:** Przy wybranym backendzie OpenVINO, blok "Serwer lokalny (llama.cpp / GGUF)" jest nadal widoczny z polami Port, Obliczenia serwera, Model (GGUF), Model (QComboBox), Szablon czatu, Wątki, Typ danych.

**Oczekiwane:** Blok powinien być ukryty LUB mieć nazwę "Backend OpenVINO" z tylko relevantnymi polami (Model, Urządzenie OpenVINO).

**Plik:** `tlumacz/qt_gui/main_window.py` — `_update_server_fields_visibility()`

**Rozwiązanie:** 
- Ukryć niepotrzebne pola przy OpenVINO (Port, Obliczenia, Szablon, Wątki, Typ danych, Model QComboBox)
- Zmienić nazwę bloku na "Backend OpenVINO — lokalny" (już jest w kodzie ale nie działa)

### 3. Pole "Klucz API" widoczne przy OpenVINO
**Problem:** Przy wybranym backendzie OpenVINO, pole "Klucz API" jest widoczne i aktywne.

**Oczekiwane:** Pole powinno być ukryte lub nieaktywne przy OpenVINO (OpenVINO nie używa klucza API).

**Plik:** `tlumacz/qt_gui/main_window.py` — `_update_server_fields_visibility()`

**Rozwiązanie:** Ukryć pole `api_key` i etykietę przy backendzie OpenVINO.

---

## Plan naprawy

1. **Naprawić `_update_server_fields_visibility()`**:
   - Dodać `is_openvino = backend == "openvino"`
   - Ukryć `api_key` i etykietę przy OpenVINO
   - Ukryć niepotrzebne pola w bloku Serwer przy OpenVINO
   - Upewnić się że nazwa bloku zmienia się na "Backend OpenVINO — lokalny"

2. **Naprawić podwójny reset**:
   - Dodać sprawdzanie czy backend już działa przed restartem
   - Ewentualnie dodać debounce na `_on_model_changed()`

---

## Funkcje do dodania

### 4. Informacja o parallel w logu
**Problem:** W oknie logu nie ma informacji ile bloków jest tłumaczonych równolegle (parallel).

**Oczekiwane:** Log powinien pokazywać:
- "Przetwarzanie 43 blok(ów) z parallel=4..."
- "Tłumaczenie bloku 1/43 (parallel 4)..."
- "Tłumaczenie bloku 2/43 (parallel 4)..."

**Plik:** `tlumacz/qt_gui/worker.py` — `TranslateWorker.run()`

**Rozwiązanie:** Dodać informację o parallel do komunikatów logu.

---

**Status:** DO NAPRAWIENIA (po zakończeniu testów OpenVINO)


---

### Naprawa przycisku restart dla OpenVINO

# TODO: Naprawa przycisku restart dla OpenVINO

**Data:** 2026-09-07
**Priorytet:** Średni
**Status:** DO NAPRAWIENIA

## Problem

Przycisk "Restart serwera" jest nieaktywny dla backendu OpenVINO.

## Przyczyna

W `main_window.py` linia 1267:
```python
self.restart_server_btn.setEnabled(bool(self._settings.server_gguf_path))
```

Przycisk jest włączony TYLKO jeśli `server_gguf_path` jest ustawione. Ale dla OpenVINO używamy `openvino_model_path`, nie `server_gguf_path`.

## Rozwiązanie

Zmienić logikę na:
```python
# Włącz restart dla WSZYSTKICH lokalnych backendów
is_local = self._settings.backend_type in ("llama", "fastapi", "openvino")
has_model = (
    (self._settings.backend_type == "llama" and self._settings.server_gguf_path) or
    (self._settings.backend_type == "fastapi" and self._settings.fastapi_model_path) or
    (self._settings.backend_type == "openvino" and self._settings.openvino_model_path)
)
self.restart_server_btn.setEnabled(is_local and has_model)
```

## Dodatkowy problem

Przy zmianie urządzenia OpenVINO (CPU → MULTI:CPU,GPU) konieczny jest restart serwera. Obecnie:
1. Użytkownik zmienia urządzenie w QComboBox
2. Zmiana nie jest automatycznie zastosowana
3. Użytkownik musi ręcznie zatrzymać i uruchomić backend

## Rozwiązanie (opcjonalne)

Dodać automatyczny restart przy zmianie urządzenia:
```python
self.server_openvino_device.currentIndexChanged.connect(self._on_openvino_device_changed)

def _on_openvino_device_changed(self, index):
    if self._backend_manager.is_running():
        # Zapytaj czy zrestartować
        reply = QMessageBox.question(...)
        if reply == QMessageBox.Yes:
            self._backend_manager.stop()
            self._backend_manager.start()
```

## Pliki do zmiany

- `tlumacz/qt_gui/main_window.py` — linia 1267 + dodanie `_on_openvino_device_changed()`

## Testy

- [ ] Przycisk restart aktywny dla OpenVINO
- [ ] Restart działa po zmianie urządzenia
- [ ] Brak regresji dla llama.cpp i FastAPI


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

### 12a. Funkcja obliczająca czas tłumaczenia 1 chunka (bloku)
**Status**: DO ZROBIENIA
**Priorytet**: Średni
**Plik**: `tlumacz/core.py`

**Problem**:
- Brak metryki czasu tłumaczenia pojedynczego chunka
- Trudno optymalizować chunk_size bez danych o czasie/chunk
- Debug.log zawiera czasy, ale nie ma funkcji w GUI

**Rozwiązanie**:
- Dodać funkcję `_calculate_avg_chunk_time()` w `core.py`
- Obliczać średni czas/chunk na podstawie debug.log
- Wyświetlać w GUI: "Średni czas/chunk: Xs"
- Pomaga dobrać optymalny chunk_size

**Kryteria akceptacji**:
- [ ] Funkcja oblicza średni czas/chunk z debug.log
- [ ] Wyświetlanie w GUI (opcjonalnie)
- [ ] Dokumentacja w README

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
**Status**: W TRAKCIE

**Zadania**:
- [ ] Dodać progress bar dla restartu serwera
- [ ] Dodać powiadomienia systemowe (gotowe tłumaczenie)
- [x] Dodać dark/light mode toggle ✅ ZAKOŃCZONE (motyw systemowy/jasny/ciemny w `theme.py`)
- [ ] Dodać skróty klawiszowe (Ctrl+R = restart serwera)
- [ ] Dodać drag & drop dla plików

### 15a. Pasek postępu — kontrast w motywie ciemnym
**Status**: DO ZROBIENIA
**Priorytet**: Niski (kosmetyczne)
**Plik**: `tlumacz/qt_gui/main_window.py` lub `tlumacz/qt_gui/theme.py`

**Problem**:
- W motywie ciemnym pasek postępu tłumaczenia jest jasnożółty
- Tekst na pasku jest biały
- Biały tekst na jasnożółtym tle jest słabo widoczny

**Rozwiązanie**:
- Zmienić kolor tekstu na ciemny (czarny/granatowy) LUB
- Zmienić kolor paska na ciemniejszy (np. pomarańczowy/czerwony) LUB
- Dodać cień/obryskowanie tekstu dla lepszej czytelności

**Kryteria akceptacji**:
- [ ] Tekst na pasku postępu jest wyraźnie widoczny w motywie ciemnym
- [ ] Nie wpływa negatywnie na motyw jasny

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

**Postęp głównych zadań**: 93% (10/11 ✅)
- Wysoki priorytet: 4/4 (100%) ✅
- Średni priorytet: 3/3 (100%) ✅
- Niski priorytet: 2/2 (100%) ✅
- OpenVINO: ✅ ZAKOŃCZONE

**Backendy**: 4/4 działają ✅
- llama.cpp ✅
- FastAPI + TranslateGemma ✅
- OpenVINO + TranslateGemma INT8 ✅
- Cloud API ✅

**UI/UX**: 1/5 zadań ✅ (dark/light mode zakończone)

**Dodatkowe zadania z do_zrobienia.md**: 11 zadań
- W trakcie: 4 (PDF round-trip, Stabilizacja, Pomoc i18n, README PL/EN)
- Planowane: 6
- Przed publikacją: 1

**Dokumentacja**: 7/7 (100%) ✅ (CHANGELOG.md zaktualizowany o OpenVINO)
**Testy**: 192/192 (100%) ✅

---

**Ostatnia aktualizacja**: 2026-09-07
**Wersja**: 0.31.0-dev
**Status**: Wersja robocza/testowa — 4 backendy działają, OpenVINO wdrożony
