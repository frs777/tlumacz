# Naprawa Przycisku Restart Serwera

## Problem

W v2 przycisk "Restart serwera" jest **nieaktywny** gdy serwer nie jest uruchomiony:

```python
# v2 (NIEPOPRAWNE)
self.restart_server_btn.setEnabled(self._server_manager.is_running)
```

To uniemożliwia uruchomienie serwera z GUI gdy `auto_start_server` jest wyłączone.

## Rozwiązanie z V1

W v1 (oryginalny projekt) przycisk był aktywny gdy:
1. Obiekt serwera istnieje (`self._server is not None`), LUB
2. (Po naszej naprawie) Plik GGUF jest skonfigurowany

```python
# v1 (POPRAWNE - po naszej naprawie)
self.restart_server_btn.setEnabled(bool(self._settings.server_gguf_path))
```

## Plan Naprawy V2

### Krok 1: Zmienić logikę setEnabled

W `main_window.py`, metoda `_build_server_settings()`:

```python
# ZAMIENIĆ:
self.restart_server_btn.setEnabled(self._server_manager.is_running)

# NA:
self.restart_server_btn.setEnabled(bool(self._settings.server_gguf_path))
```

### Krok 2: Dodać metodę _update_restart_button_label()

```python
def _update_restart_button_label(self) -> None:
    """Update restart button label and tooltip based on server state."""
    if self._server_manager.is_running:
        self.restart_server_btn.setText(t("button.restart_server"))
        self.restart_server_btn.setToolTip(
            "Zatrzymaj zarządzany llama-server i uruchom go ponownie "
            "z aktualnymi ustawieniami."
        )
    else:
        self.restart_server_btn.setText(t("button.start_server"))
        self.restart_server_btn.setToolTip(
            "Uruchom zarządzany llama-server z aktualnymi ustawieniami."
        )
```

### Krok 3: Wywołać _update_restart_button_label()

1. Po `_build_server_settings()` przy inicjalizacji
2. Po każdej zmianie stanu serwera (w `_on_server_state_changed()`)
3. Po restarcie (w `_on_server_restart_succeeded()` i `_on_server_restart_failed()`)

### Krok 4: Zmienić _on_restart_server()

W v2, `_on_restart_server()` oddelegowuje do ServerManager. Ale gdy serwer nie istnieje, trzeba go najpierw utworzyć:

```python
def _on_restart_server(self) -> None:
    """Restart or start the managed llama-server."""
    logger.info("_on_restart_server() called")
    
    # Utwórz serwer jeśli nie istnieje (gdy auto_start_server było wyłączone)
    if self._server_manager.server is None:
        logger.info("_on_restart_server(): creating server from settings")
        settings = self._collect_settings()
        server = LlamaServer(
            ServerConfig(
                port=settings.server_port,
                parallel=settings.server_parallel,
                compute_mode=settings.server_compute_mode,
                gguf_path=settings.server_gguf_path,
                chat_template=settings.server_chat_template or "",
            )
        )
        self._server_manager.set_server(server)
    
    # ... reszta kodu (oddelegowanie do ServerManager)
```

### Krok 5: Dodać metodę set_server() do ServerManager

```python
class ServerManager(QObject):
    # ...
    
    def set_server(self, server: LlamaServer) -> None:
        """Set the server instance (used when server doesn't exist yet)."""
        self._server = server
        self._state = ServerState.IDLE
        self.state_changed.emit(self._state)
```

---

## Kod do Przeniesienia z V1

### 1. main_window.py - _build_server_settings()

```python
# V1 (po naprawie):
self.restart_server_btn = QPushButton(t("button.restart_server"))
self.restart_server_btn.setObjectName("restartServerBtn")
self.restart_server_btn.setToolTip(
    "Zatrzymaj zarządzany llama-server i uruchom go ponownie "
    "z aktualnymi ustawieniami."
)
self.restart_server_btn.clicked.connect(self._on_restart_server)
# Przycisk aktywny gdy jest skonfigurowany plik GGUF (niezależnie od stanu serwera)
self.restart_server_btn.setEnabled(bool(self._settings.server_gguf_path))
self._update_restart_button_label()
self.server_form.addRow(self.restart_server_btn)
```

### 2. main_window.py - _update_restart_button_label()

```python
def _update_restart_button_label(self) -> None:
    """Update restart button label and tooltip based on server state."""
    if self._server is not None and self._server.is_running():
        self.restart_server_btn.setText(t("button.restart_server"))
        self.restart_server_btn.setToolTip(
            "Zatrzymaj zarządzany llama-server i uruchom go ponownie "
            "z aktualnymi ustawieniami."
        )
    else:
        self.restart_server_btn.setText(t("button.start_server"))
        self.restart_server_btn.setToolTip(
            "Uruchom zarządzany llama-server z aktualnymi ustawieniami."
        )
```

### 3. main_window.py - _on_restart_server() (pierwsza część)

```python
def _on_restart_server(self) -> None:
    """Restart or start the managed llama-server using the current GUI settings."""
    logger.info("_on_restart_server() called")
    # Create server if it doesn't exist
    if self._server is None:
        logger.info("_on_restart_server(): creating server from settings")
        settings = self._collect_settings()
        self._server = LlamaServer(
            ServerConfig(
                port=settings.server_port,
                parallel=settings.server_parallel,
                compute_mode=settings.server_compute_mode,
                gguf_path=settings.server_gguf_path,
                chat_template=settings.server_chat_template or "",
            )
        )
    # ... reszta kodu
```

### 4. i18n.py - tłumaczenia

```python
# Polskie:
"button.restart_server": "Restart serwera",
"button.start_server": "Uruchom serwer",

# Angielskie:
"button.restart_server": "Restart server",
"button.start_server": "Start server",
```

---

## Testowanie

Po naprawie:

1. **Wyłącz auto_start_server** w ustawieniach
2. **Zrestartuj aplikację**
3. **Przejdź do zakładki "API i serwer"**
4. **Sprawdź przycisk** - powinien być AKTYWNY i mówić "Uruchom serwer"
5. **Kliknij przycisk** - serwer powinien się uruchomić
6. **Sprawdź przycisk ponownie** - powinien mówić "Restart serwera"

---

## Status

- [x] Zidentyfikowano problem
- [x] Znaleziono rozwiązanie w v1
- [x] Udokumentowano plan naprawy
- [ ] Przeniesiono kod do v2
- [ ] Przetestowano w GUI
- [ ] Zaktualizowano STATUS.md

---

**Data**: 2026-09-04
**Priorytet**: Wysoki
**Szacowany czas**: 30 minut
