# Zarządzanie serwerem — Tłumacz

**Wersja:** 0.21.0-dev  
**Data ostatniej aktualizacji:** 2026-09-05

---

## Spis treści

1. [Przegląd architektury](#przegląd-architektury)
2. [ServerManager — centralny zarządca](#servermanager--centralny-zarządca)
3. [Przycisk multifunkcyjny „Restart serwera"](#przycisk-multifunkcyjny-restart-serwera)
4. [Obsługa llama.cpp](#obsługa-llamacpp)
5. [Zarządzanie procesem](#zarządzanie-procesem)
6. [Obsługa osieroconych procesów](#obsługa-osieroconych-procesów)
7. [Szablony czatu](#szablony-czatu)
8. [Konfiguracja zaawansowana](#konfiguracja-zaawansowana)

---

## Przegląd architektury

### Ewolucja: V1 → V2

W wersji V1 zarządzanie serwerem było rozproszone — `MainWindow` bezpośrednio operował na `LlamaServer`, używając trzech niezależnych flag (`_server`, `_server_op_thread`, `_server_running`). Prowadziło to do:

- **Race conditions** — thread mógł być niszczony zanim się zakończył
- **Osieroconych procesów** — po crashu aplikacji `llama-server` pozostał uruchomiony
- **Niespójnych stanów** — flagi mogły być niesynchronizowane
- **Crash przy anulowaniu** — próba uruchomienia serwera w złym stanie

### Architektura V2 — ServerManager

W wersji V2 wprowadzono **ServerManager** — centralny komponent oparty na wzorcu **State Machine**:

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

---

## ServerManager — centralny zarządca

### Maszyna stanów

ServerManager utrzymuje jawny stan serwera:

```
         ┌──────────┐
         │   IDLE   │ ← brak serwera lub zatrzymany
         └────┬─────┘
              │ start()
              ▼
       ┌──────────────┐
       │   STARTING   │ ← w trakcie uruchamiania
       └──────┬───────┘
              │ sukces
              ▼
        ┌──────────┐
        │ RUNNING  │ ← serwer działa
        └────┬─────┘
             │ stop()
             ▼
       ┌──────────────┐
       │   STOPPING   │ ← w trakcie zatrzymywania
       └──────┬───────┘
              │ zakończone
              ▼
         ┌──────────┐
         │   IDLE   │
         └──────────┘
```

### Sygnały

ServerManager emituje sygnały Qt, na które reaguje GUI:

| Sygnał | Opis |
|--------|------|
| `server_started(base_url)` | Serwer uruchomiony pomyślnie |
| `server_stopped()` | Serwer zatrzymany |
| `server_error(message)` | Błąd operacji |
| `operation_finished()` | Zakończono operację (start/stop/restart) |

### Operacje

#### start()

Uruchamia serwer z konfiguracji:

```python
def start(self) -> None:
    if self._state != ServerState.IDLE:
        return  # operacja niedozwolona w tym stanie
    self._state = ServerState.STARTING
    self._server = LlamaServer(self._config)
    self._run_operation(StartWorker(self._server))
```

#### stop()

Zatrzymuje działający serwer:

```python
def stop(self) -> None:
    if self._state != ServerState.RUNNING:
        return
    self._state = ServerState.STOPPING
    self._run_operation(StopWorker(self._server))
```

#### restart(config_updates)

Restartuje serwer z nową konfiguracją:

```python
def restart(self, config_updates: dict) -> None:
    if self._state == ServerState.RUNNING:
        self._state = ServerState.STOPPING
        self._run_operation(RestartWorker(self._server, config_updates))
    elif self._state == ServerState.IDLE:
        # Serwer istnieje (utworzony ręcznie) — uruchom go
        if self._server is not None:
            for key, value in config_updates.items():
                setattr(self._server.config, key, value)
            self._state = ServerState.STARTING
            self._run_operation(StartWorker(self._server))
        else:
            self.start()
```

### Kolejka operacji

ServerManager zapobiega równoległym operacjom:

```python
def _run_operation(self, worker: ServerWorker) -> None:
    # Sprawdź czy poprzednia operacja jeszcze trwa
    if self._thread is not None and self._thread.isRunning():
        logger.warning("Previous thread still running, skipping")
        return
    
    # 1. Zabij osierocone procesy na porcie
    self._kill_orphaned_processes()
    
    # 2. Utwórz thread i worker
    self._worker = worker
    self._thread = QThread()
    self._worker.moveToThread(self._thread)
    
    # 3. Połącz sygnały
    self._thread.started.connect(self._worker.run)
    self._worker.success.connect(self._on_operation_success)
    self._worker.error.connect(self._on_operation_error)
    self._worker.finished.connect(self._thread.quit)
    self._thread.finished.connect(self._cleanup_thread)
    
    # 4. Uruchom
    self._thread.start()
```

---

## Przycisk multifunkcyjny „Restart serwera"

### Opis

Przycisk multifunkcyjny to **inteligentny przycisk** w zakładce „API i serwer", który zmienia etykietę i zachowanie w zależności od:

1. **Stanu serwera** (działa / zatrzymany)
2. **Checkboxa „Uruchamiaj serwer razem z programem"** (zaznaczony / odznaczony)

### Cztery stany przycisku

| Stan serwera | Auto-start | Etykieta przycisku | Akcja po kliknięciu |
|--------------|------------|-------------------|---------------------|
| ✅ Działa | ✅ Zaznaczony | **Restart serwera** | Zatrzymaj i uruchom ponownie z aktualnymi ustawieniami |
| ✅ Działa | ❌ Odznaczony | **Zatrzymaj serwer** | Tylko zatrzymaj |
| ❌ Zatrzymany | ✅ Zaznaczony | **Uruchom serwer** | Uruchom z aktualnymi ustawieniami |
| ❌ Zatrzymany | ❌ Odznaczony | **Zaznacz box 'Uruchamiaj serwer razem z programem'** | Pokaż komunikat informacyjny |

### Implementacja

#### Aktualizacja etykiety

```python
def _update_restart_button_label(self) -> None:
    """Update restart button label, tooltip and enabled state."""
    box_checked = self.auto_start_server.isChecked()
    is_running = self._server_manager.is_running

    if is_running and box_checked:
        self.restart_server_btn.setText(t("button.restart_server"))
        self.restart_server_btn.setToolTip(
            "Zatrzymaj zarządzany llama-server i uruchom go ponownie "
            "z aktualnymi ustawieniami."
        )
    elif is_running and not box_checked:
        self.restart_server_btn.setText(t("button.stop_server"))
        self.restart_server_btn.setToolTip(
            "Zatrzymaj zarządzany llama-server."
        )
    elif not is_running and box_checked:
        self.restart_server_btn.setText(t("button.start_server"))
        self.restart_server_btn.setToolTip(
            "Uruchom zarządzany llama-server z aktualnymi ustawieniami."
        )
    else:  # not is_running and not box_checked
        self.restart_server_btn.setText(t("button.check_auto_start"))
        self.restart_server_btn.setToolTip(
            "Aby uruchomić serwer, zaznacz opcję "
            "„Uruchamiaj serwer razem z programem"."
        )
    
    # Przycisk ZAWSZE aktywny
    self.restart_server_btn.setEnabled(True)
```

#### Obsługa kliknięcia

```python
def _on_restart_server(self) -> None:
    """Handle the smart restart button."""
    box_checked = self.auto_start_server.isChecked()
    is_running = self._server_manager.is_running

    # Case 4: Stopped + box unchecked → show info message
    if not is_running and not box_checked:
        QMessageBox.information(
            self,
            "Serwer lokalny",
            "Aby uruchomić serwer, zaznacz opcję "
            "„Uruchamiaj serwer razem z programem".",
        )
        return

    # Stop any active translation thread
    if self._is_thread_running(self._thread):
        self._thread.stop()
    self._thread = None

    # Check if operation already in progress
    if self._server_manager.state in (ServerState.STARTING, ServerState.STOPPING):
        self._append_log("Operacja na serwerze już trwa.")
        return

    # Create server if it doesn't exist
    if self._server_manager.server is None:
        settings = self._collect_settings()
        server = LlamaServer(ServerConfig(...))
        self._server_manager.server = server
        self._server_manager._state = ServerState.IDLE

    # Save settings
    settings = self._collect_settings()
    save_settings(settings)
    config_updates = self._build_config_updates()

    # Case 1: Running + box checked → restart
    if is_running and box_checked:
        self.restart_server_btn.setEnabled(False)
        self._append_log("Restart llama-server...")
        self._server_manager.restart(config_updates)

    # Case 2: Running + box unchecked → stop
    elif is_running and not box_checked:
        self.restart_server_btn.setEnabled(False)
        self._append_log("Zatrzymywanie llama-server...")
        self._server_manager.stop()

    # Case 3: Stopped + box checked → start
    elif not is_running and box_checked:
        self.restart_server_btn.setEnabled(False)
        self._append_log("Uruchamianie llama-server...")
        self._server_manager.restart(config_updates)
```

### Kluczowe cechy

1. **Zawsze aktywny** — przycisk nigdy nie jest zablokowany (`setEnabled(True)`)
2. **Dynamiczna etykieta** — zmienia się w zależności od stanu
3. **Bezpieczny** — sprawdza czy operacja już trwa, zatrzymuje aktywne tłumaczenie
4. **Elastyczny** — tworzy serwer na żądanie jeśli nie istnieje
5. **Zapisuje ustawienia** — przed operacją zapisuje aktualne ustawienia GUI

### Kiedy używać

| Scenariusz | Akcja |
|------------|-------|
| Zmieniłeś ustawienia serwera (port, GGUF, szablon) | Kliknij **„Restart serwera"** |
| Serwer się zawiesił | Kliknij **„Restart serwera"** |
| Chcesz zatrzymać serwer | Odznacz auto-start → kliknij **„Zatrzymaj serwer"** |
| Chcesz uruchomić serwer ręcznie | Zaznacz auto-start → kliknij **„Uruchom serwer"** |
| Nie wiesz co zrobić | Kliknij przycisk — pokaże się podpowiedź |

---

## Obsługa llama.cpp

### LlamaServer — zarządzanie procesem

Klasa `LlamaServer` w `tlumacz/server.py` zarządza procesem `llama-server`:

#### Uruchamianie serwera

```python
def start(self) -> Optional[str]:
    """Start llama-server, retrying with fallback templates if needed."""
    binary = shutil.which("llama-server")
    if binary is None:
        raise ServerStartError("Nie znaleziono 'llama-server' w PATH.")
    
    if not self.config.gguf_path:
        raise ServerStartError("Brak ścieżki do pliku GGUF modelu.")
    
    # Sprawdź czy port jest zajęty przez osierocony proces
    if self._is_port_busy():
        self._kill_port_occupier()
    
    # Próba uruchomienia z różnymi szablonami
    for template in self._template_attempts():
        self._process = subprocess.Popen(
            self._command(binary, template),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if self._wait_ready():
            return template  # zwraca szablon który zadziałał
    
    raise ServerStartError(f"Serwer nie uruchomił się: {last_error}.")
```

#### Linia komend

```python
def _command(self, binary: str, chat_template: Optional[str]) -> list[str]:
    """Build the llama-server command line."""
    command = [
        binary,
        "-m", self.config.gguf_path,
        "--alias", "local",           # model alias dla API
        "--host", self.config.host,
        "--port", str(self.config.port),
        "--ctx-size", str(self.config.effective_ctx_size()),
        "--parallel", str(self.config.parallel),
    ]
    
    # Tryb obliczeń
    if self.config.compute_mode == "cpu":
        command += ["--n-gpu-layers", "0"]
    else:
        command += ["--n-gpu-layers", "999", "--split-mode", "none"]
    
    # Szablon czatu
    if chat_template:
        command += ["--no-jinja", "--chat-template", chat_template]
    else:
        command.append("--jinja")
    
    return command
```

#### Health check

```python
def is_running(self) -> bool:
    """Return True if an OpenAI-compatible endpoint responds on our port."""
    url = f"{self.config.base_url}/models"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except (OSError, ValueError):
        return False
```

#### Zatrzymywanie serwera

```python
def stop(self) -> None:
    """Terminate the managed llama-server subprocess."""
    if self._process is None:
        if self.is_running():
            self._kill_by_port()  # zabij osierocony proces
        return
    
    if self._process.poll() is None:
        try:
            self._process.terminate()
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)
    
    self._process = None
    
    # Sprawdź czy serwer HTTP nadal odpowiada
    if self.is_running():
        self._kill_by_port()
```

---

## Zarządzanie procesem

### Cykl życia procesu

1. **Start** — `subprocess.Popen` z `start_new_session=True` (izolacja)
2. **Ready check** — odpytywanie `/v1/models` co 0.5s przez 60s
3. **Running** — serwer odpowiada na żądania API
4. **Stop** — SIGTERM → wait 10s → SIGKILL → wait 5s
5. **Cleanup** — sprawdzenie czy port jest wolny

### Eskalacja zatrzymywania

```
SIGTERM → wait 10s → SIGKILL → wait 5s → _kill_by_port()
```

### Timeouty

| Operacja | Timeout |
|----------|---------|
| Uruchomienie serwera | 60s |
| Zatrzymanie (SIGTERM) | 10s |
| Zatrzymanie (SIGKILL) | 5s |
| Health check | 2s |

---

## Obsługa osieroconych procesów

### Problem

Po crashu aplikacji lub nieprawidłowym zamknięciu proces `llama-server` może pozostać uruchomiony, blokując port.

### Rozwiązanie

Przed każdą operacją ServerManager wywołuje `_kill_orphaned_processes()`:

```python
def _kill_orphaned_processes(self) -> None:
    """Zabij osierocone procesy llama-server na porcie."""
    port = self._config.port
    
    # Użyj ss do znalezienia PID
    result = subprocess.run(
        ["ss", "-tlnp", f"sport = :{port}"],
        capture_output=True, text=True, timeout=5
    )
    
    for line in result.stdout.splitlines():
        if "pid=" in line:
            match = re.search(r"pid=(\d+)", line)
            if match:
                pid = int(match.group(1))
                # Nie zabijaj naszego procesu
                if self._server is not None and pid == self._server._process.pid:
                    continue
                # Zabij osierocony proces
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                try:
                    os.kill(pid, 0)  # sprawdź czy nadal istnieje
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass  # proces się zakończył
```

### Narzędzia systemowe

| Narzędzie | Zastosowanie |
|-----------|--------------|
| `ss -tlnp` | Znalezienie PID na porcie (Linux) |
| `lsof -ti :PORT` | Alternatywa dla `ss` (macOS/BSD) |
| `SIGTERM` | Łagodne zatrzymanie |
| `SIGKILL` | Wymuszone zatrzymanie |

---

## Szablony czatu

### Automatyczny fallback

Jeśli serwer nie uruchomi się z wybranym szablonem, Tłumacz automatycznie próbuje alternatywne:

```python
def _template_attempts(self) -> list[Optional[str]]:
    """Candidate chat templates in order."""
    primary = self.config.chat_template or None
    
    # "translategemma" używa natywnego jinja (Gemma 3)
    if primary == "translategemma":
        primary = None
    
    attempts = [primary]
    for candidate in ("chatml", None):
        if candidate != primary and candidate not in attempts:
            attempts.append(candidate)
    
    return attempts
```

**Kolejność prób:**
1. Wybrany szablon (np. `chatml`)
2. `chatml` (jeśli nie był wybrany)
3. `None` (natywny jinja)

### Profile modeli

Tłumacz zapamiętuje który szablon zadziałał dla danego modelu:

```json
{
  "model_profiles": {
    "qwen2.5-coder:7b": {
      "chat_template": "chatml"
    },
    "translategemma-4b": {
      "chat_template": "translategemma"
    }
  }
}
```

---

## Konfiguracja zaawansowana

### ServerConfig

```python
@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 18080
    gguf_path: str = ""
    ctx_size: int = 8192
    parallel: int = 1
    compute_mode: str = "gpu"  # "gpu" lub "cpu"
    chat_template: str = ""    # "", "chatml", "translategemma"
    extra_args: list[str] = []
```

### effective_ctx_size

Każdy slot równoległy wymaga osobnego kontekstu:

```python
def effective_ctx_size(self, chunk_size: int = 4000) -> int:
    """Return context size large enough for all parallel slots."""
    tokens_per_slot = max(4096, chunk_size // 3 + 2048)
    return max(self.ctx_size, self.parallel * tokens_per_slot)
```

**Przykład:**
- `parallel=1`, `chunk_size=4000` → `ctx_size=8192`
- `parallel=4`, `chunk_size=4000` → `ctx_size=16384`

### Tryb GPU vs CPU

| Tryb | Parametry | Kiedy używać |
|------|-----------|--------------|
| **gpu** | `--n-gpu-layers 999 --split-mode none` | Karta graficzna z VRAM |
| **cpu** | `--n-gpu-layers 0` | Brak GPU lub mały VRAM |

**Uwaga:** `--n-gpu-layers 999` oznacza „offloaduj maksymalnie ile się da". Jeśli nie ma wystarczającej ilości VRAM, llama-server automatycznie dostosuje liczbę warstw.

### Aliasy modelu

Zarządzany serwer startuje z `--alias local`, więc żądania API muszą używać modelu `local`:

```json
{
  "model": "local",
  "messages": [...]
}
```

To upraszcza konfigurację — nie musisz znać nazwy modelu GGUF.

---

## Diagnostyka

### Logi

ServerManager loguje wszystkie operacje:

```
INFO: ServerManager.start(): starting server
INFO: LlamaServer.start() called, port=18080
INFO: Process started, PID=12345
INFO: _wait_ready(): server ready after 15 attempts
INFO: ServerManager._on_operation_success(): result=None
```

### Typowe problemy

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Timeout po 60s | Serwer nie odpowiada | Sprawdź ścieżkę GGUF, port, RAM |
| Port zajęty | Osierocony proces | `_kill_orphaned_processes()` (automatyczne) |
| Crash przy starcie | Uszkodzony plik GGUF | Sprawdź integralność pliku |
| Brak odpowiedzi | Zły szablon czatu | Automatyczny fallback lub zmiana szablonu |

---

## Licencja

MIT — zobacz [LICENSE.txt](../../LICENSE.txt)

## Autor

frs — https://github.com/frs777/tlumacz
