# Debug Qt/GUI — analiza z 2026-09-01

Analiza wykonana skillami `qt-threading` i `qt-crash-debug`
(`/home/frs/.agents/skills/`), na podstawie niezacommitowanych zmian
w repo (parallel translation, izolacja tłumaczenia w procesie,
przycisk restartu serwera).

Klasyfikacja: **Hang** (proces żyje, ale nie odpowiada w rozsądnym
czasie), nie crash. Nie crash dump / nie forced kill.

## Ustalenia (potwierdzone w kodzie)

### A. `parallel` niepodłączony do GUI
`core.py` ma gotowy `ThreadPoolExecutor`, `config.py` ma pole
`server_parallel`, ale GUI wszędzie wymusza `parallel=1` na sztywno
(`main_window.py:911,1193,1367`) i nie ma widgetu do jego zmiany.
Help (linia 580) opisuje kontrolkę, która nie istnieje.
**Decyzja użytkownika: zostaje jak jest — kod parallel istnieje na
potrzeby testów, planowane usunięcie w przyszłości.**

### B. `server.start()`/`stop()` blokują wątek GUI
`server.py:_wait_ready()` to pętla `time.sleep(0.5)` do 60 s,
`stop()` czeka do 15 s (`terminate`+`wait(10)`, `kill`+`wait(5)`).
Wołane bezpośrednio z wątku GUI w:
- `_ensure_server_after_cancel()` — bez `processEvents()`,
- `_on_restart_server()` — `processEvents()` tylko raz przed startem,
  nie w trakcie pętli oczekiwania.

Łamie zasadę z `qt-threading`: nie blokować wątku UI na
network/subprocess call. **Do naprawy: przenieść restart/stop
serwera na wątek roboczy, zachowując przycisk „Restart serwera”
w GUI.**

### C. `QThread.terminate()` jako fallback anulowania — niebezpieczne
`_force_cancel_thread()` (2 s po anulowaniu) woła
`thread.thread.terminate()`. Flagowane jako *critical* przez
`qt_thread_scout.py` i `thread-lifetime-guide.md`. Dla wątku Pythona
to gorsze niż w C++ — CPython nie ma bezpiecznego przerwania wątku
w dowolnym miejscu bajtkodu, więc wymuszone zabicie może uszkodzić
stan interpretera. **Do naprawy: bezpieczny sposób na natychmiastowe
przerwanie tłumaczenia bez `QThread.terminate()`.**

### D. Pierwotny hang z `blad.md` — przyczyna wciąż nieznana
Stary `max_tokens = max(2048, len(chunk)*3//4)` mógł pozwalać
modelowi generować bardzo długo przy pętli powtórzeń bez EOS. Nowy
kod ogranicza to do `min(1024, ...)` — łagodzi objaw (krótszy worst
case), ale nie tłumaczy, *dlaczego* konkretny chunk wpada w pętlę.
**Do zaproponowania: rozwiązanie diagnostyczne/zabezpieczające.**

### E. Cancel w trybie równoległym nie przerywa startniętych zapytań
W `core.py:translate_file`, przy `parallel>1`, anulowanie woła tylko
`future.cancel()` (działa jedynie na zadania jeszcze niewystartowane).
Zadania już wykonujące się czekają w
`with ThreadPoolExecutor(...) as executor:`, którego `__exit__`
domyślnie `wait=True` — blokuje aż do zakończenia wszystkich wątków,
zanim `TranslationCancelledError` poleci dalej. Obecnie nieszkodliwe
(cały proces i tak zabijany z zewnątrz), ale ukryta pułapka przy
użyciu `Translator` poza izolowanym procesem (testy, przyszłe CLI).
**Do naprawy: cancel ma realnie przerywać już wystartowane taski.**

## Ranking ważności
1. B — pewne, łatwe do odtworzenia zamrożenie GUI do 60 s.
2. C — ryzyko uszkodzenia stanu interpretera przy anulowaniu.
3. D — złagodzone, ale przyczyna źródłowa nieustalona.
4. E — pułapka logiczna, obecnie bez wpływu na produkcję.
(A — świadomie pominięte, kod zostaje na potrzeby testów.)

## Status realizacji
- [x] B — restart/stop serwera poza wątkiem GUI, przycisk zostaje
  (`ServerRestartWorker`/`ServerRestartThread` w `worker.py`,
  `_on_restart_server` i `_ensure_server_after_cancel` w `main_window.py`)
- [x] C — bezpieczne natychmiastowe przerwanie tłumaczenia
  (`multiprocessing` + kooperatywny cancel przez `cancel_event`,
  eskalacja terminate/kill w `TranslateWorker.run()` na QThread,
  `QThread.terminate()` tylko jako ostateczność przy zamknięciu aplikacji)
- [x] D — propozycja rozwiązania diagnostycznego
  (`_log_chunk_timing()` w `core.py` → `~/.config/tlumacz/debug.log`,
  loguje chunk_len, max_tokens, elapsed; SLOW chunks mają preview)
- [x] E — realne przerywanie wystartowanych tasków przy cancel
  (`Translator.cancel()` zamyka aktywne HTTP clients,
  `executor.shutdown(wait=False, cancel_futures=True)` przy parallel>1)
