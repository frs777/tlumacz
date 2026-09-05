# ADR-001: Architektura ServerManager

**Data:** 2026-09-04  
**Status:** Zaakceptowane  
**Autor:** Architekt oprogramowania

## Kontekst

Aplikacja Tłumacz zarządza lokalnym serwerem `llama-server` do tłumaczenia dokumentów. Obecna architektura ma następujące problemy:

1. **Osierocone procesy** — po crashu aplikacji proces `llama-server` pozostaje uruchomiony
2. **Race conditions** — `QThread.finished` jest emitowane, ale thread może być jeszcze "running"
3. **Niespójne stany** — trzy flagi (`_server`, `_server_op_thread`, `_server_running`) mogą być niesynchronizowane
4. **Crash przy anulowaniu** — `_ensure_server_after_cancel` próbuje uruchomić serwer w złym stanie
5. **Crash przy starcie w chmurze** — brak rozróżnienia między serwerem lokalnym a chmurą

## Decyzja

Zastąpić obecny system zarządzania serwerem architekturą opartą na wzorcu **State Machine** z centralnym `ServerManager`.

### Nowa architektura

```
┌─────────────────────────────────────────────────────────────┐
│                        MainWindow                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              ServerManager (QObject)                  │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  State: IDLE | STARTING | RUNNING | STOPPING    │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                         │                              │  │
│  │         ┌───────────────┼───────────────┐              │  │
│  │         ▼               ▼               ▼              │  │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐          │  │
│  │   │StartWorker│   │StopWorker│   │RestartWorker│       │  │
│  │   └──────────┘   └──────────┘   └──────────┘          │  │
│  │         │               │               │              │  │
│  │         └───────────────┼───────────────┘              │  │
│  │                         ▼                              │  │
│  │                  ┌────────────┐                        │  │
│  │                  │  QThread   │                        │  │
│  │                  └────────────┘                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│              ┌──────────────────┐                           │
│              │  LlamaServer     │                           │
│              │  - _process      │                           │
│              │  - start()       │                           │
│              │  - stop()        │                           │
│              │  - is_running()  │                           │
│              └──────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### Kluczowe zasady

1. **Jeden zarządca** — `ServerManager` jest jedynym punktem kontaktu dla GUI
2. **Jawne stany** — `State.IDLE/STARTING/RUNNING/STOPPING` zamiast wielu flag
3. **Non-blocking** — wszystkie operacje w tle, GUI nigdy nie blokuje
4. **Pełne czyszczenie** — `_on_operation_finished` zawsze czeka na thread i czyści referencje
5. **Obsługa osieroconych** — `_kill_orphaned_processes` przed każdą operacją
6. **Sygnały** — GUI reaguje na zdarzenia, nie odpytuje stanu

### Komponenty

#### ServerManager
- Zarządza cyklem życia serwera
- Utrzymuje jawny stan (State enum)
- Uruchamia operacje w tle przez ServerWorker
- Obsługuje osierocone procesy przez `_kill_orphaned_processes`
- Emituje sygnały: `server_started`, `server_stopped`, `server_error`, `operation_finished`

#### ServerWorker (bazowa klasa)
- `StartWorker` — uruchamia serwer
- `StopWorker` — zatrzymuje serwer
- `RestartWorker` — restartuje serwer z nową konfiguracją
- Każdy worker działa w osobnym QThread
- Emituje: `finished`, `success`, `error`

#### LlamaServer
- Zarządza procesem `llama-server`
- `_is_port_busy()` — sprawdza czy port jest zajęty
- `_kill_port_occupier()` — zabija osierocony proces
- `start()` — uruchamia serwer (sprawdza port przed startem)
- `stop()` — zatrzymuje serwer (sprawdza port po stopie)

## Konsekwencje

### Pozytywne
- ✅ Jasny model stanów — łatwiejsze debugowanie
- ✅ Brak race conditions — thread jest zawsze czekany
- ✅ Obsługa osieroconych procesów — automatyczne czyszczenie
- ✅ Rozszerzalność — łatwo dodać nowe operacje
- ✅ Testowalność — ServerManager można testować izolowanie

### Negatywne
- ⚠️ Wymaga przepisania MainWindow — ryzyko regressji
- ⚠️ Więcej kodu — ServerManager + ServerWorker + 3 workery
- ⚠️ Złożoność — nowi deweloperzy muszą zrozumieć architekturę

### Neutralne
- ℹ️ Zachowana kompatybilność — `_server` jako alias do `_server_manager.server`
- ℹ️ Zachowane logowanie — wszystkie operacje logowane

## Migracja

1. **Faza 1:** Dodać ServerManager i ServerWorker do `worker.py` ✅
2. **Faza 2:** Dodać `_is_port_busy` i `_kill_port_occupier` do `LlamaServer` ✅
3. **Faza 3:** Przepisać `MainWindow` żeby używał `ServerManager`
4. **Faza 4:** Usunąć stary kod (`ServerRestartThread`, stare callbacki)
5. **Faza 5:** Zaktualizować testy

## Testy

- Wszystkie istniejące testy muszą przechodzić
- Dodać testy dla ServerManager (stany, przejścia, obsługa błędów)
- Dodać testy dla `_kill_orphaned_processes`
- Dodać testy integracyjne (start → stop → restart)

## Referencje

- [Qt Threading](https://doc.qt.io/qt-6/thread-basics.html)
- [State Machine Pattern](https://en.wikipedia.org/wiki/State_pattern)
- [Observer Pattern](https://en.wikipedia.org/wiki/Observer_pattern)
