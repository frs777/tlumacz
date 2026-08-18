# Tłumacz

Narzędzie do tłumaczenia dokumentów oparte na AI z **interfejsem graficznym Qt (PySide6)**. Tłumaczy pliki Markdown/tekstowe na polski (lub inny obsługiwany język) przy użyciu dowolnego API zgodnego z OpenAI — testowane z lokalnym serwerem Ollama/llama.cpp.

> [Polski (PL)](README.md) · [English (EN)](README.en.md)

## Wersja

Aktualna wersja: **0.5.1**

## Funkcje

- 🖥️ **Interfejs graficzny Qt** zbudowany na PySide6 / Qt Widgets
- 📄 **Wybór plików** wejściowych i wyjściowych
- ⚙️ **Konfigurowalne API**: adres bazowy, klucz API, model, rozmiar fragmentów, temperatura, język docelowy
- 🔄 **Tłumaczenie w tle** w osobnym wątku — interfejs nigdy nie zamraża się
- ▶️ **Zarządzany serwer lokalny** — aplikacja może sama uruchomić `llama-server` na wydzielonym porcie (domyślnie 18080) ze wskazanym plikiem GGUF i zatrzymać go przy zamykaniu
- ⏹️ **Anulowanie** trwającego tłumaczenia w dowolnym momencie
- 📊 **Pasek postępu** i podgląd logów na żywo
- 👁️ **Podgląd** przetłumaczonego tekstu
- 💾 **Ustawienia trwałe** w `~/.config/tlumacz/config.json`
- 🎨 **Ciemny motyw QSS** z dołączoną ikoną SVG

## Wymagania

- Python 3.10+
- `PySide6`, `openai` (instalowane automatycznie przez pip/AUR)
- Opcjonalnie: `llama-server` dla wbudowanego zarządzanego serwera

## Instalacja

### Ze źródeł (rozwój)

```bash
pip install -e .
tlumacz
```

### Budowanie wheel

```bash
python -m build --wheel
```

### Arch Linux (AUR)

Repozytorium zawiera gotowy `PKGBUILD`. Pakiet możesz zbudować przez:

```bash
makepkg -si
```

Zależności są rozwiązywane z oficjalnych repozytoriów (`pyside6`) i AUR (`python-openai`).
Po instalacji uruchom aplikację globalnie przez `tlumacz` lub z menu aplikacji.

## Użycie

1. Uruchom `tlumacz`
2. Wybierz **plik wejściowy** do przetłumaczenia
3. Wybierz **plik wyjściowy** (domyślnie `nazwa_<język>.rozszerzenie`, np. `nazwa_pl.md`)
4. W razie potrzeby dostosuj **ustawienia API** (domyślnie: `http://127.0.0.1:8080/v1`, model `qwen2.5-coder-7b-instruct-q5_k_m`)
5. Kliknij **Tłumacz**
6. Obserwuj postęp w logach, a następnie przejrzyj wynik w panelu **podglądu**

### Zarządzany serwer

W `~/.config/tlumacz/config.json` ustaw:

```json
{
  "auto_start_server": true,
  "server_port": 18080,
  "server_gguf_path": "/ścieżka/do/model.gguf"
}
```

Aplikacja uruchomi wtedy `llama-server` w tle na tym porcie, ustawi na niego
adres API i zatrzyma serwer przy zamknięciu okna.

## Zgodność API

Aplikacja używa protokołu OpenAI Chat Completions, więc działa z:

- Lokalnymi serwerami Ollama / llama.cpp (`http://127.0.0.1:8080/v1`)
- Chmurowymi punktami końcowymi zgodnymi z OpenAI

## Rozwój

```bash
# Testy / podstawowe sprawdzenia
python -c "from tlumacz.qt_gui.app import main; print('OK')"

# Uruchomienie GUI bez wyświetlacza (sprawdzenie headless)
QT_QPA_PLATFORM=offscreen python -m tlumacz.qt_gui.app
```

## Struktura projektu

```
tlumacz/
├── core.py                # Logika tłumaczenia wielokrotnego użytku (bez zależności Qt)
├── server.py              # Zarządzany proces llama-server (bez zależności Qt)
└── qt_gui/
    ├── app.py             # Punkt wejścia (main())
    ├── config.py          # Trwałe ustawienia użytkownika
    ├── main_window.py     # Główne okno Qt Widgets
    ├── worker.py          # Worker QThread do tłumaczenia w tle
    └── resources/         # Motyw QSS + ikona SVG
```

## Licencja

MIT