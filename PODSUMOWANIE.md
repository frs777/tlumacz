# Podsumowanie projektu — Tłumacz

**Data:** 2 września 2026
**Repozytorium:** https://github.com/frs777/tlumacz
**Wersja:** 0.19.1
**Status:** wersja robocza/testowa; brak publikacji 0.19.1 w publicznym AUR.

---

## Aktualny stan

Projekt jest aplikacją Qt/PySide6 do tłumaczenia dokumentów przez API zgodne z OpenAI oraz przez zarządzany lokalny `llama-server` z modelem GGUF.

Najważniejsza funkcja projektu — **tłumaczenie** — działa, ale jakość zależy od modelu. W testach Hy-MT2-1.8B-Q4_K_S okazał się bardzo szybki, lecz przy dokumentach wielojęzycznych pozostawia część treści w języku źródłowym. Większe modele dawały lepszą jakość, ale były wolniejsze.

### Testy formatów

- **Markdown/TXT/HTML:** działają, ale HTML i dokumenty wielojęzyczne wymagają dalszego wzmocnienia promptów.
- **DOCX:** round-trip zachowuje strukturę dokumentu; jakość językowa Hy-MT2 jest nierówna.
- **ODT:** round-trip działa; główne kryterium oceny to zachowanie struktury/formatowania.
- **EPUB:** round-trip działa i zachowuje strukturę archiwum, ale test wielojęzyczny ujawnił pozostawione fragmenty chińskie/angielskie.

### Modele

- **Hy-MT2-1.8B-Q4_K_S** — obecny szybki model testowy; dobry do testów pipeline'u i wydajności, ale prawdopodobnie za słaby do docelowej jakości.
- **TranslateGemma** — lepsza jakość w dotychczasowych testach, lecz wyraźnie wolniejszy.
- **Salamandra 2B** — odłożona; testy sugerowały potrzebę specjalnej obsługi.

---

## Zrealizowane funkcje

### GUI

- wybór wejścia/wyjścia i ustawień API,
- tłumaczenie w QThread bez blokowania GUI,
- anulowanie, pasek postępu, log i podgląd,
- trwały `config.json` z walidacją i backupami,
- zakładki Tłumaczenie / Ustawienia / Pomoc,
- motywy system/light/dark,
- własny prompt,
- **stoper tłumaczenia** — zaimplementowany,
- pomoc PL/EN,
- tooltipy i tabela parametrów,
- **checkbox "Czyść cache po tłumaczeniu"** — domyślnie włączony,
- **przycisk "Restart serwera"** — naprawiony, działa po tłumaczeniu (naprawiono błąd `RuntimeError: QThread already deleted`).

### Zarządzany llama-server

`tlumacz/server.py` zarządza procesem `llama-server`, ścieżką GGUF, portem i profilem szablonu rozmowy. Obsługiwany jest autofallback `jinja`/`chatml`, a działający szablon jest zapisywany w `model_profiles`.

**Obecne zachowanie:** zarządzany serwer startuje przy uruchomieniu aplikacji i jest zatrzymywany przy jej zamknięciu.

**Restart serwera:** przycisk w Ustawieniach zatrzymuje serwer i uruchamia go ponownie z aktualnymi parametrami, bez restartowania GUI. Po restarcie sprawdza API `/v1/models` i zgłasza sukces/błąd.

---

## Tłumaczenie i preprocessing

`core.py` obsługuje chunking, prompt, skille, glosariusz, `max_tokens`, ochronę i przywracanie elementów technicznych oraz wykrywanie tekstu już będącego w języku docelowym.

`preprocess.py` chroni kod, URL-e i tagi XML/HTML placeholderami, filtruje linie i dzieli dokumenty sekcjami. Dla XML stosowane jest dzielenie po znakach bez rozcinania placeholderów.

Wbudowane skille obejmują Markdown, plaintext, HTML, PDF, DOCX, ODT i EPUB. Skille mogą pochodzić także z `~/.config/tlumacz/skills/`.

### Wydajność

Zaimplementowano usprawnienia wydajności:
- **Cache tłumaczeń** (SQLite) — unika powtarzania tych samych zapytań, z automatycznym czyszczeniem po tłumaczeniu
- **Równoległe tłumaczenie chunków** (ThreadPoolExecutor) — równoległe wysyłanie zapytań do serwera
- **Skalowanie `max_tokens`** — proporcjonalne do `chunk_size` zamiast stałego limitu
- **Statystyki cache** — wyświetlane w logach (hits/misses, effectiveness)

---

## Round-trip dokumentów

DOCX/ODT/EPUB są przetwarzane z zachowaniem oryginalnego formatu. Tłumaczony jest tekst w odpowiednich węzłach, a struktura, style, tabele i pliki nietreściowe są zachowywane.

PDF obecnie nie ma pełnego round-trip; OCR dla skanów i powrót do PDF pozostają na liście zadań.

---

## Pakowanie i snapshot

- **0.19.1** została skompilowana jako `tlumacz-0.19.1-1-any.pkg.tar.zst`.
- Paczka znajduje się w `/home/frs/RepoArch/x86_64` i została dodana do lokalnego `moje-repo.db`.
- **0.19.1 nie jest przeznaczona do publicznego AUR** — to wczesna wersja testowa.
- Utworzony został snapshot/tag `snapshot-20260823-pre-aur` przed dalszymi eksperymentami.
- Publiczny AUR pozostaje bez tej wersji.

---

## Testy

Test suite obejmuje obecnie 102 testy: config, profile modeli, skille, preprocessing, ekstrakcję i round-trip DOCX/ODT/EPUB, serwer, cache oraz GUI smoke tests.

Przed kolejnym wydaniem wymagane są ponowne testy tłumaczenia, szczególnie na dokumentach wielojęzycznych oraz wszystkich formatach round-trip.

---

## Najbliższy plan

1. ~~Dodać **Restart serwera** w Ustawieniach~~ — zaimplementowano.
2. ~~Nie zmieniać działającego stopera~~ — jest już gotowy.
3. ~~Dodać **czyszczenie cache po tłumaczeniu**~~ — zaimplementowano.
4. Testować nowe modele 2B na ODT i EPUB.
5. Wzmocnić prompty dla formatów, szczególnie dokumentów wielojęzycznych.
6. Wybrać model zapewniający rozsądny kompromis jakość/szybkość.
7. Dopiero po stabilizacji rozważać kolejne wydanie i publiczne AUR.

Pełna lista: [do_zrobienia.md](do_zrobienia.md).
