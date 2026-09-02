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
- [x] **Szablon skilla dla użytkowników** — `SKILL_TEMPLATE.md` i przycisk „Nowy skilla...”.
- [x] **Skille PDF / DOCX / ODT / EPUB** — ekstrakcja i reguły formatów.
- [x] **Round-trip EPUB / DOCX / ODT (1:1)** — zachowanie struktury i plików nietreściowych.
- [ ] **PDF round-trip** — powrót z przetłumaczonego tekstu do PDF.
- [ ] **OCR dla skanów PDF i obrazów (Tesseract)** — OCR + obsługa png/jpg/webp/bmp.

### Wyniki testów modeli — stan roboczy

- **Hy-MT2-1.8B-Q4_K_S** — obecny szybki model testowy. Tłumaczy, ale przy trudniejszych/wielojęzycznych dokumentach pozostawia fragmenty w języku źródłowym lub miesza języki. Jest jednak wyraźnie szybszy od dotychczas testowanych większych modeli.
- **DOCX / ODT / EPUB** — round-trip formatów działa; głównym kryterium testów jest zachowanie struktury/formatowania, a nie tylko jakość językowa.
- **EPUB** — struktura przechodzi, ale test na wielojęzycznym dokumencie pokazał pozostawione fragmenty chińskie/angielskie. Nie traktować jako dowodu uszkodzenia pipeline'u formatu.
- **TranslateGemma** — wyższa jakość niż Hy-MT2, ale znacznie wolniejsza w dotychczasowych testach.
- **Salamandra 2B** — odrzucona do dalszych testów; wyniki wskazywały na potrzebę specjalnego oprogramowania/obsługi.

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
