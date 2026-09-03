# Do zrobienia — tlumacz

Lista pomysłów i niedokończonych usprawnień projektu **tlumacz**.

## Konfiguracja (config.json)

- [ ] **Pełna edycja config.json przez GUI** — jawny przycisk **Zapisz ustawienia** oraz autozapis przy zmianie pól.
- [ ] **Lista modeli z serwera** — pobierać modele z `GET /v1/models`; lokalny llama.cpp używa aliasu `local`.
- [x] **Ścieżka do pliku GGUF** — `server_gguf_path`, `server_port`, `auto_start_server` + `LlamaServer`.
- [x] **Własny prompt użytkownika** — pole w ustawieniach.
- [x] **Walidacja config.json** — backup uszkodzonego/nieprawidłowego configu i wartości domyślne.
- [x] **Wstrzykiwanie skilli** — skille formatów i własne skille użytkownika.
- [x] **Przywracanie domyślnych opcji** — backup configu przed przywróceniem.
- [x] **Odporność na zmianę modelu** — autofallback szablonu i `model_profiles`.
- [x] **Czyszczenie cache po tłumaczeniu** — opcja `cache_clear_after_translation` w GUI i configu (domyślnie włączona).
- [ ] **Detekcja przez próbę modelu** — mikro-zapytanie wykrywające EOS / tryb myślenia i automatyczne dostrojenie.

## Interfejs (GUI)

- [ ] **Wskaźnik trwającej pracy** — animowany spinner podczas tłumaczenia.
- [x] **Licznik czasu tłumaczenia** — stoper startuje po *Tłumacz* i zatrzymuje się po zakończeniu/anulowaniu.
- [x] **Restart zarządzanego serwera llama.cpp z GUI** — przycisk w Ustawieniach: zatrzymanie bieżącego `llama-server`, ponowne odczytanie aktualnych parametrów GUI/config i start serwera z nową konfiguracją, bez restartu całej aplikacji. Po restarcie sprawdza dostępność API `/v1/models` i pokazuje wynik użytkownikowi. Naprawiono błąd `RuntimeError: QThread already deleted` po tłumaczeniu.

## Dokumentacja / pomoc

- [x] **Krótka pomoc w GUI (PL + EN)** — formaty, config, LLM, serwer lokalny i nazwy plików.
- [x] **Szczegółowa pomoc dla każdej funkcji** — tooltipy i tabela parametrów w Pomocy PL/EN.

## Lokalizacja (i18n)

- [ ] **Struktura i18n** — PL + EN z możliwością dodawania języków bez zmian w kodzie.
- [ ] **UI aplikacji** — przetłumaczyć wszystkie widoczne ciągi GUI na pl/en.
- [ ] **Pomoc w GUI** — przenieść treść Pomocy do systemu i18n.
- [ ] **Dokumentacja** — zsynchronizować README PL/EN i PODSUMOWANIE.
- [ ] **Format plików tłumaczeń** — ustalić format i test kompletności kluczy.

## Tłumaczenie

- [x] **Wydajność** — ograniczyć czas tłumaczenia; dopasować `max_tokens` do `chunk_size` zamiast stałego limitu. Zaimplementowano:
  - Cache tłumaczeń (SQLite) z automatycznym czyszczeniem
  - Równoległe tłumaczenie chunków (ThreadPoolExecutor)
  - Skalowanie `max_tokens` proporcjonalnie do `chunk_size`
  - Statystyki cache w logach (hits/misses)
- [ ] **Wbudowane skille rozpoznawane po rozszerzeniu** — stosować automatycznie; GUI ma służyć głównie do skilli dodatkowych/własnych.
- [x] **Wykrywanie języka wejściowego** — realizowane przez prompt.
- [x] **Glosariusz / słownik** — CSV + wpisy z GUI.
- [x] **Motyw (theme)** — dzień / noc / system.
- [x] **Wzorce pomijania per typ pliku** — skille + wzorce domyślne + własne regexy.
- [x] **Szablon skilla dla użytkowników** — `SKILL_TEMPLATE.md` i przycisk „Nowy skilla...".
- [x] **Skille PDF / DOCX / ODT / EPUB** — ekstrakcja i reguły formatów.
- [x] **Round-trip EPUB / DOCX / ODT (1:1)** — zachowanie struktury i plików nietreściowych.
- [ ] **PDF round-trip** — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR). **W trakcie wdrażania.**
- [ ] **OCR dla skanów PDF i obrazów (Tesseract)** — OCR + obsługa png/jpg/webp/bmp. **Architektura przygotowana pod przyszłe dodanie.**

### Bug: skill ODT niekompatybilny z kodem — NAPRAWIONY (3 września 2026)

**Problem:** Skill ODT (`tlumacz/skills/odt.md`) opisywał tłumaczenie "tekstu skonwertowanego do Markdown", ale kod (`_translate_document_xml`) tłumaczy **węzły XML in-place**, nie Markdown. Model dostawał sprzeczne instrukcje → wyciek promptów, halucynacje, nieprzetłumaczone sekcje.

**Naprawiono:**
- [x] Zaktualizowano skill ODT — opisuje XML in-place, nie Markdown
- [x] Naprawiono `_translate_document_xml` — dodano obsługę `.tail` dla zagnieżdżonych elementów
- [x] Dodano test regresji — testy ODT przechodzą

### Wyniki testów modeli — stan na 3 września 2026

Szczegółowy raport: `jakosc_tlumaczenia_v0.20.0.md`

- **Hy-MT2-1.8B-Q4_K_S (GPU)** — 4:15, jakość 70%, ucinanie tłumaczenia. Szybki ale za słaby jakościowo.
- **Hy-MT2-7B-Q4_K_M + glosariusz (GPU)** — 19:05, jakość 75%, nadal ucinanie. **Dyskwalifikacja** — 4.4x wolniej niż 1.8B.
- **TranslateGemma-4b-it.Q4_K_M (GPU)** — 10:17, jakość 87%, kompletne tłumaczenie. **ZWYCIĘZCA** — najlepszy kompromis jakość/szybkość.
- **TranslateGemma-4b-it.Q4_K_M (CPU)** — 11:31, jakość 87%, ale ucinanie 40% treści. Problem nie związany z GPU/CPU — prawdopodobnie stan serwera lub cache.
- **Salamandra 2B** — odrzucona do dalszych testów; wyniki wskazywały na potrzebę specjalnego oprogramowania/obsługi.

**Pipeline hybrydowy (Hy-MT2-1.8B + TranslateGemma-4b) — porzucony 2 września 2026:**
- Działał dobrze tylko dla Markdown (~2 min, ~99.7% jakości).
- Dla formatów binarnych (ODT/DOCX) generował śmieci: powtarzający się tekst, wyciek promptów, nieprzetłumaczone fragmenty.
- Tłumaczenie in-place XML nie nadaje się dla słabszego modelu etapu 1.
- Rezygnacja: główny przypadek użycia (dokumenty naukowe/prawne w ODT/DOCX) nie działał.

**Wnioski:**
- TranslateGemma-4b na GPU jest optymalnym wyborem dla codziennego użytku (87% jakości, 10:17 czas)
- Hy-MT2-1.8B jest za słaby jakościowo nawet jako model wstępny (70% jakości, generuje śmieci w XML)
- Problem ucinania na CPU wymaga dalszego badania (te same skills, ten sam chunk 4000)
- Stare (krótsze) skills dają lepsze rezultaty niż rozszerzone (uniknąć podwojenia promptu)

## Pakowanie / repo

- [x] **Lokalna paczka testowa 0.19.1** — zbudowana i dodana do `/home/frs/RepoArch/x86_64/moje-repo.db`; nie publikować tej wczesnej wersji w publicznym AUR.
- [ ] **Aktualizacja URL w PKGBUILD** — zweryfikować przed przyszłą publikacją AUR.
- [ ] **Automatyczna synchronizacja moje-repo** — skrypt dodający nową paczkę po buildzie.
- [ ] **Paczki DEB / RPM / AppImage**.

## GitHub

- [x] **README domyślny po polsku** — `README.md` + link do `README.en.md`.
- [ ] **Ikona repo / social preview** — og-image.

## Stabilizacja przed publicznym wydaniem

- [ ] Ustabilizować podstawową funkcję: niezawodne tłumaczenie dokumentów we wszystkich obsługiwanych formatach.
- [ ] Poprawić prompty dla Markdown/HTML/DOCX/ODT/EPUB, szczególnie dokumentów wielojęzycznych.
- [ ] Przetestować lepsze modele 2B przed wyborem modelu domyślnego.
- [ ] Nie publikować wczesnych wersji testowych w publicznym AUR; publikacja dopiero po stabilizacji podstawowej funkcji.
