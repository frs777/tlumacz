# Tłumacz

Narzędzie do tłumaczenia dokumentów oparte na AI z **interfejsem graficznym Qt (PySide6)**. Tłumaczy pliki Markdown/tekstowe na polski (lub inny obsługiwany język) przy użyciu dowolnego API zgodnego z OpenAI — testowane z lokalnym serwerem Ollama/llama.cpp.

> [Polski (PL)](README.md) · [English (EN)](README.en.md)

## Wersja

Aktualna wersja: **0.20.1-2**

> ⚠️ **Wersja wczesna / testowa.** Jakość tłumaczenia zależy od użytego modelu LLM.
> Obecnie najlepsze wyniki daje **TranslateGemma-4b** (~87% jakości).
> Słabsze modele (poniżej 7B parametrów) mogą generować niekompletne tłumaczenia,
> halucynacje i artefakty — szczególnie w formatach binarnych (DOCX, ODT, EPUB, PDF).
> Nie publikować w publicznym AUR przed stabilizacją.

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

### Pakiety binarne

Pobierz z [GitHub Releases v0.20.1](https://github.com/frs777/tlumacz/releases/tag/v0.20.1):

| Format | Plik | Budowanie |
|--------|------|-----------|
| **AUR** | [`tlumacz-0.20.1-2-any.pkg.tar.zst`](https://github.com/frs777/tlumacz/releases/download/v0.20.1/tlumacz-0.20.1-2-any.pkg.tar.zst) | `makepkg -si` |
| **RPM** | [`tlumacz-0.20.1-2.noarch.rpm`](https://github.com/frs777/tlumacz/releases/download/v0.20.1/tlumacz-0.20.1-2.noarch.rpm) | `rpmbuild -bb tlumacz.spec` |
| **DEB** | [`tlumacz_0.20.1-2_all.deb`](https://github.com/frs777/tlumacz/releases/download/v0.20.1/tlumacz_0.20.1-2_all.deb) | `dpkg-buildpackage -us -uc -b` |
| **AppImage** | [`tlumacz-0.20.1-2-x86_64.AppImage`](https://github.com/frs777/tlumacz/releases/download/v0.20.1/tlumacz-0.20.1-2-x86_64.AppImage) | `appimagetool AppDir tlumacz.AppImage` |

### Wymagania systemowe

**Wszystkie pakiety** wymagają:
- Python 3.10+
- PySide6 (Qt 6)
- python-openai
- python-pymupdf (od v0.20.1)
- hicolor-icon-theme

**AppImage** wymaga jawnego zainstalowania powyższych zależności.

### Narzędzia do pakowania

| Format | Narzędzie | Instalacja (Arch) |
|--------|-----------|-------------------|
| AUR | `makepkg` | wbudowane w pacman |
| RPM | `rpmbuild` | `rpm-build` |
| DEB | `dpkg-buildpackage` | `dpkg-dev` |
| AppImage | `appimagetool` | [GitHub releases](https://github.com/AppImage/AppImageKit/releases) |

### Ekstrakcja pakietów

| Format | Komenda |
|--------|---------|
| AUR/RPM | `bsdtar -xf pakiet.pkg.tar.zst` / `rpm2cpio pakiet.rpm \| cpio -id` |
| DEB | `dpkg-deb -x pakiet.deb katalog/` |
| AppImage | `./pakiet.AppImage --appimage-extract` |
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