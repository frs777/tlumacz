# Podsumowanie projektu — Tłumacz

**Data:** 3 września 2026
**Repozytorium:** https://github.com/frs777/tlumacz
**Wersja:** 0.20.0
**Status:** wersja robocza/testowa; brak publikacji w publicznym AUR.

---

## Aktualny stan

Projekt jest aplikacją Qt/PySide6 do tłumaczenia dokumentów przez API zgodne z OpenAI oraz przez zarządzany lokalny `llama-server` z modelem GGUF.

Najważniejsza funkcja projektu — **tłumaczenie** — działa, ale jakość zależy od modelu. Po serii testów (wrzesień 2026) wybrano TranslateGemma-4b jako optymalny kompromis jakość/szybkość.

### Testy formatów (3 września 2026)

Wszystkie formaty tekstowe działają poprawnie po serii napraw:

- **Markdown/TXT:** ✅ działają poprawnie
- **HTML:** ✅ działa poprawnie (naprawiono placeholdery `⟦PROT_N⟧` → `[PROT_N]`)
- **DOCX:** ✅ round-trip zachowuje strukturę dokumentu
- **ODT:** ✅ round-trip działa (naprawiono bug z `.tail` w zagnieżdżonych elementach)
- **EPUB:** ✅ round-trip działa (naprawiono strukturę XHTML, dodano `_translate_xhtml_inplace`)
- **PDF:** ⏳ w trakcie wdrażania — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR)

### Naprawione bugi (3 września 2026)

1. Separatory `⟦S_%d⟧` → numerowane `⟦S_0⟧`, `⟦S_1⟧` w `_translate_document_xml`
2. Obsługa `.tail` dla ODT (tekst w zagnieżdżonych elementach)
3. `_strip_eos_tokens` — regexy w dowolnym miejscu + `<|file_separator|>`
4. Prompt główny uproszczony (usunięto "preserving Markdown formatting")
5. Skill ODT i EPUB zaktualizowane
6. `_translate_xhtml_inplace` — nowa metoda dla EPUB/HTML
7. `max_tokens` — mnożnik 2048 → 3072
8. Placeholdery `⟦PROT_N⟧` → `[PROT_N]` (model lepiej radzi sobie z nawiasami)

### Plan wdrożenia PDF

**Cel:** Tłumaczenie PDF z zachowaniem układu (tekstowe, bez OCR).

**Zależności:** PyMuPDF (dodany do `pyproject.toml`).

**Fazy:**
1. Ekstrakcja tekstu z pozycjami (PyMuPDF)
2. Tłumaczenie z zachowaniem struktury
3. Wstawianie tekstu z powrotem do PDF
4. Integracja z GUI
5. Testy

**Architektura pod OCR:** Interfejs `TextExtractor` z implementacją `PyMuPDFExtractor` i przyszłą `OCRExtractor`.

### Modele — wyniki testów (2 września 2026)

Szczegółowy raport: `jakosc_tlumaczenia_v0.20.0.md`

| Model | Tryb | Czas | Jakość | Status |
|-------|------|------|--------|--------|
| Hy-MT2-1.8B-Q4_K_S | GPU | 4:15 | 70% | ❌ Ucinanie |
| Hy-MT2-7B-Q4_K_M + glos | GPU | 19:05 | 75% | ❌ Dyskwalifikacja (wolny) |
| **TranslateGemma-4b-it.Q4_K_M** | **GPU** | **10:17** | **87%** | ✅ **ZWYCIĘZCA** |
| TranslateGemma-4b-it.Q4_K_M | CPU | 11:31 | 87% | ⚠️ Ucinanie 40% (do zbadania) |
| Salamandra 2B | — | — | — |  Odrzucona |

**Wybrany model:** TranslateGemma-4b-it.Q4_K_M na GPU (87% jakości, 10:17 czas, kompletne tłumaczenie)

### Pipeline Hybrydowy — PORZUCONY

Próba wdrożenia pipeline'u "wstępne tłumaczenie + korekta" (Hy-MT2-1.8B → TranslateGemma-4b) zakończyła się niepowodzeniem i kod został usunięty (2 września 2026).

**Dlaczego nie zadziałało:**
- Działał poprawnie **tylko dla Markdown** (~2 min, ~99.7% jakości)
- Dla **ODT/DOCX** (główny przypadek użycia — dokumenty naukowe/prawne) generował kompletny śmieć: powtarzający się tekst, wyciek promptów, nieprzetłumaczone fragmenty, mieszankę języków
- Przyczyna: tłumaczenie in-place XML generuje krótkie, fragmentaryczne segmenty — Hy-MT2-1.8B (70% jakości) halucynuje na takich danych, a TranslateGemma nie była w stanie tego skorygować
- **Wniosek**: nie ma sensu utrzymywać funkcji hybrydowej tylko dla Markdown; główny przypadek użycia (dokumenty binarne) nie działał

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
4. ~~Wybrać model~~ — TranslateGemma-4b-it.Q4_K_M na GPU (87% jakości, 10:17).
5. **Zbadać problem ucinania na CPU** — te same skills i chunk 4000 co GPU, ale 40% treści ucięte.
6. **Zoptymalizować wykorzystanie CPU** — obecne obciążenie ~60%, możliwość równoległości.
7. Wzmocnić prompty dla formatów, szczególnie dokumentów wielojęzycznych.
8. Dopiero po stabilizacji rozważać kolejne wydanie i publiczne AUR.

Pełna lista: [do_zrobienia.md](do_zrobienia.md).
