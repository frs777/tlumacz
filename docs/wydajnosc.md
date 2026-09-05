# Rekomendacje wydajnościowe — Tłumacz

**Data:** 2 września 2026
**Wersja projektu:** 0.19.1
**Status:** wdrożone — Opcja A (ThreadPoolExecutor) + cache + skalowanie max_tokens

---

## Główne wąskie gardło

`tlumacz/core.py` tłumaczy chunki **sekwencyjnie** w pętli, a zarządzany `llama-server` w `tlumacz/server.py` domyślnie startuje z `--parallel 1`. Oznacza to, że nawet gdybyśmy wysyłali zapytania asynchronicznie, serwer i tak kolejkowałby je po sobie. W efekcie duży plik to dziesiątki minut czekania.

---

## Opcje usprawnień (od najtańszych do najbardziej złożonych)

### 1. Zwiększenie `--parallel` na `llama-server`

- Dodać w ustawieniach opcję **„Liczba slotów równoległych”** (`parallel`).
- Przy zwiększeniu `parallel` trzeba proporcjonalnie zwiększyć `ctx_size`, bo sloty dzielą context.
- Przykład orientacyjny: `parallel=4`, `chunk_size=2000` znaków, `ctx_size=16384`.
- Ryzyko: na słabszym sprzęcie (mało RAM/VRAM) może zabraknąć zasobów — opcja musi być konfigurowalna i mieć ostrzeżenie.

**Status:** Nie zaimplementowano — użytkownik testował `parallel=1-4` na AMD GPU z 500MB VRAM, brak korzyści.

### 2. Równoległe tłumaczenie chunków w jednym pliku

#### Opcja A — `concurrent.futures.ThreadPoolExecutor` (wybrana i zaimplementowana)

Najmniej inwazyjna metoda. Główny wątek dzieli dokument na chunki, przekazuje je do puli wątków, a następnie zbiera wyniki w oryginalnej kolejności i zapisuje do pliku wyjściowego.

- **Zalety:**
  - mało zmian w istniejącym kodzie,
  - dobrze współgra z `QThread` GUI,
  - GIL nie przeszkadza przy I/O do API.
- **Wady:**
  - mniej efektywny niż asyncio przy bardzo dużej liczbie zapytań,
  - wymaga synchronizacji wyników i anulowania.

**Status:** ✅ Zaimplementowano w `core.py` z `ThreadPoolExecutor(max_workers=parallel)`.

#### Opcja B — `asyncio` + `openai.AsyncOpenAI`

Bardziej wydajna przy dużej liczbie równoległych zapytań, ale wymaga integracji z pętlą zdarzeń Qt (np. `qasync`) lub osobnym wątkiem z event loop asyncio.

- **Zalety:** niski narzut, łatwa kontrola nad `Semaphore`.
- **Wady:** więcej zmian architektonicznych, trudniejsze anulowanie.

**Status:** Nie zaimplementowano.

#### Opcja C — osobne procesy workerów (`multiprocessing`)

Każdy chunk lub podzbiór chunków trafia do osobnego procesu.

- **Zalety:** omija GIL, izoluje błędy.
- **Wady:** narzut na serializację, trudniejsze anulowanie, większe zużycie RAM. Dla lokalnego API przerost.

**Status:** Nie zaimplementowano.

### 3. Równoległe tłumaczenie wielu plików

Jeśli użytkownik tłumaczy katalogi lub partie plików, każdy plik może być przetwarzany w osobnym workerze. To prostsze niż równoległość chunków, ale wymaga uporządkowania logów i paska postępu.

**Status:** Nie zaimplementowano.

### 4. Streaming

`stream=True` nie skraca całkowitego czasu tłumaczenia, ale poprawia responsywność UI. Przy równoległym przetwarzaniu streaming komplikuje kolejność zapisywania — sugerowane jako opcjonalna funkcja później.

**Status:** Nie zaimplementowano.

### 5. Cache tłumaczeń

W dokumentach technicznych często powtarzają się identyczne frazy, nagłówki i stopki. Cache per chunk (hash treści + konfiguracja) mógłby zaoszczędzić sporo zapytań. Prosty cache w pamięci lub SQLite na dysku.

**Status:** ✅ Zaimplementowano w `cache.py` (SQLite) z automatycznym czyszczeniem po tłumaczeniu (opcja `cache_clear_after_translation`).

### 6. Skalowanie `max_tokens`

Dopasowanie `max_tokens` do `chunk_size` zamiast stałego limitu.

**Status:** ✅ Zaimplementowano — `max_tokens = max(256, int(1024 * chunk_ratio))`.

---

## Wybrana strategia implementacji

**Zaimplementowano:**
1. ✅ Cache tłumaczeń (SQLite) z automatycznym czyszczeniem
2. ✅ Równoległe tłumaczenie chunków (ThreadPoolExecutor)
3. ✅ Skalowanie `max_tokens` proporcjonalnie do `chunk_size`
4. ✅ Statystyki cache w logach (hits/misses, effectiveness)
5. ✅ Opcja `cache_clear_after_translation` w GUI (domyślnie włączona)

**Nie zaimplementowano:**
- Zwiększenie `parallel` na llama-server (testowane, brak korzyści na słabym GPU)
- Równoległe tłumaczenie wielu plików
- Streaming

### Pipeline Hybrydowy — PORZUCONY (2 września 2026)

Próba przyspieszenia tłumaczenia przez podział na dwa etapy (szybki model wstępny + korekta) **nie powiodła się** i została wycofana.

**Plan:** Hy-MT2-1.8B (szybki, 70% jakości) tłumaczy wstępnie → TranslateGemma-4b (wolniejszy, 87% jakości) koryguje.

**Wyniki:**
- **Markdown:** ~2 min, ~99.7% jakości — działało świetnie
- **ODT/DOCX:** 1:16:06, jakość ~0% — kompletna katastrofa

**Dlaczego nie zadziałało dla formatów binarnych:**
1. Tłumaczenie in-place XML (węzły tekstowe w ZIP) produkuje krótkie, oderwane fragmenty tekstu
2. Hy-MT2-1.8B na takich fragmentach halucynuje — powtarza ten sam akapit 15+ razy, ignoruje instrukcje, miesza języki
3. TranslateGemma-4b w etapie 2 nie była w stanie skorygować tak zniszczonego wejścia — tylko przepuszczała śmieć dalej
4. Wyciek promptów systemowych do wyjścia ("Proszę o poprawione tłumaczenie:")

**Wniosek architektoniczny:** Pipeline hybrydowy wymaga modelu wstępnego o jakości ≥85% żeby generować użyteczne wejście dla korekty. Ale jeśli model wstępny ma 85%+ jakości, to drugi etap korekty jest zbędny — można od razu użyć tego modelu. **Pipeline hybrydowy nie ma sensu ekonomicznego** dla dostępnych modeli.

**Kod usunięty** — nie ma co utrzymywać martwego kodu.

---

## Bug: skill ODT niekompatybilny z kodem (3 września 2026)

Skill ODT (`tlumacz/skills/odt.md`) opisuje tłumaczenie "tekstu skonwertowanego do Markdown", ale `_translate_document_xml` tłumaczy węzły XML in-place. Model dostaje sprzeczne instrukcje.

**Wyniki testów (test3.odt, 2150 znaków, EN+FR+DE):**

| Konfiguracja | Czas | Jakość |
|---|---|---|
| Ze skillem ODT (stary, 1644 znaki) | 4:30 | Wyciek promptów, FR/DE nieprzetłumaczone |
| Bez skilla ODT | 1:05 | Dobre tłumaczenie |
| Nowy krótki skill ODT (450 znaków) | 5:50 | Halucynacje, powtórzenia x10 |
| Hy-MT2-1.8B ręcznie (prosty prompt) | 1-2 min | Najlepszy wynik |

**Wniosek:** Skill ODT pogarsza jakość. Kod trzeba naprawić — łączyć węzły XML w większe segmenty lub zaktualizować skill.

---

## Uwagi techniczne

- `llama-server` z `--parallel N` alokuje N slotów KV-cache. Żeby sloty były wykorzystane, musi nadejść co najmniej N równoczesnych zapytań.
- Przy lokalnym serwerze na CPU zbyt duża liczba slotów może spowolnić generowanie przez kontekst switching; wartość domyślna powinna pozostać `1` i być podnoszona świadomie przez użytkownika.
- Przy zewnętrznym API (OpenAI, Groq itp.) równoległość też pomaga, ale trzeba uwzględnić rate limity.
- Należy unikać tworzenia nowego klienta OpenAI dla każdego chunka w trybie równoległym — lepiej użyć jednego klienta na worker lub `AsyncOpenAI` z limitem połączeń.
- Cache jest automatycznie czyszczony po każdym tłumaczeniu (domyślnie) aby nie fałszować wyników testów wydajności i dokładności.

---

## Pełna lista zadań

Zobacz aktualny plan implementacji i postęp w osobnym pliku planu (jeśli istnieje) lub w TODO list.
