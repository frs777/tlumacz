# Podsumowanie projektu — Tłumacz

**Data:** 19 sierpnia 2026
**Repozytorium:** https://github.com/frs777/tlumacz (publiczne)
**Wersja:** 0.5.1
**Paczka w moje-repo:** `tlumacz-0.5.1-1-any` (Arch, `/home/frs/RepoArch/x86_64`)

---

## Co to jest

Narzędzie do tłumaczenia dokumentów oparte na AI z interfejsem graficznym
**Qt (PySide6)**. Tłumaczy pliki Markdown/tekstowe na wybrany język (domyślnie
polski) przez dowolne API zgodne z OpenAI — w tym przez wbudowany, zarządzany
serwer lokalny `llama-server` (GGUF).

## Zrealizowane funkcje

### Interfejs (Qt GUI, v0.5.0)
- Wybór plików wejściowych/wyjściowych, ustawienia API (adres, klucz, model,
  rozmiar fragmentów, temperatura, język docelowy)
- Tłumaczenie w tle (QThread, `worker.py`) — UI nigdy się nie zawiesza
- Anulowanie tłumaczenia, pasek postępu, log na żywo, podgląd wyniku
- Trwałe ustawienia w `~/.config/tlumacz/config.json`
- Ciemny motyw QSS + ikona SVG (zasoby pakowane razem z wheelem)

### Zarządzany serwer lokalny (v0.5.1)
- `tlumacz/server.py` — `LlamaServer` startuje `llama-server` w tle na
  wydzielonym porcie (domyślnie **18080**) ze wskazanym plikiem **GGUF**
- Serwer zatrzymywany przy zamknięciu okna; dodatkowo sprzątanie przez
  `atexit` i handler SIGTERM/SIGINT
- Pola configu: `server_port`, `server_gguf_path`, `auto_start_server`

### Ścieżka wyjściowa (v0.5.1)
- Przy każdym wyborze pliku wejściowego generowana jest domyślna ścieżka
  wyjściowa z sufiksem języka: `plik.md` → `plik_pl.md`, `plik_en.md` itd.
- Zmiana języka docelowego w GUI aktualizuje sufiks domyślnej ścieżki

## Struktura kodu

```
tlumacz/
├── core.py                # Logika tłumaczenia (bez zależności Qt)
├── server.py              # Zarządzany proces llama-server (bez zależności Qt)
└── qt_gui/
    ├── app.py             # Punkt wejścia (main()), start/stop serwera
    ├── config.py          # Trwałe ustawienia (config.json)
    ├── main_window.py     # Główne okno Qt Widgets
    ├── worker.py          # Worker QThread do tłumaczenia w tle
    └── resources/         # Motyw QSS + ikona SVG
```

## Pakowanie / dystrybucja

- **Wheel PyPI:** `python -m build --wheel` → `dist/tlumacz-0.5.1-py3-none-any.whl`
- **AUR:** gotowy `PKGBUILD` (nazwa `tlumacz`, arch `any`, zależności:
  python, pyside6, python-openai, hicolor-icon-theme)
- **moje-repo:** paczka `tlumacz-0.5.1-1-any` w `/home/frs/RepoArch/x86_64`
  (repo `moje-repo`, `SigLevel = Optional TrustAll`)

## Konfiguracja (config.json)

```json
{
  "base_url": "http://127.0.0.1:18080/v1",
  "model": "qwen2.5-coder-7b-instruct-q5_k_m",
  "target_language": "Polish",
  "server_port": 18080,
  "server_gguf_path": "/var/lib/ollama/blobs/sha256-...",
  "auto_start_server": true
}
```

Uwaga: lokalny serwer (llama.cpp) **ignoruje** nazwę modelu — zawsze używa
`local`, dostępnego z `GET /v1/models`.

## Historia wersji (git)

| Commit | Opis |
|--------|------|
| `6bf9159` | v0.1.0 — podstawowe CLI z historią wiadomości |
| `ca3a1af` | v0.2.0 — integracja LLM z czatem |
| `b3fc43f` | v0.3.0 — obsługa narzędzi (czytanie plików, URL) |
| `057ce04` | v0.4.0 — wyświetlanie informacji o wywołaniach narzędzi |
| `b1cdb3e` | v0.5.0 — Qt GUI dla tłumaczenia dokumentów |
| `0ca20e0` | rename projektu: agent-translator → **tlumacz** |
| `2579dac` | polski README |
| `5b772cc` | roadmapa (`do_zrobienia.md`) |
| `0d0e05d` | v0.5.1 — zarządzany serwer + ścieżki z sufiksem języka |

## Plan (do_zrobienia.md)

- Pełna edycja config.json przez GUI (przycisk Zapisz + autozapis)
- Lista modeli z serwera (`GET /v1/models`) zamiast pola tekstowego
- Pola GGUF/port w GUI (obecnie tylko przez config.json)
- Własny prompt użytkownika, walidacja config.json
- Pomoc PL/EN w GUI
- Wykrywanie języka wejściowego (przez prompt LLM)
- Glosariusz — własny plik CSV + wpisy z GUI
- Motyw dzień / noc / system
- Paczki DEB / RPM / AppImage
- Skrypt automatycznej synchronizacji moje-repo
- Ikona repo / og-image

## Uwagi środowiskowe

- Konto GitHub: `frs777` (classic PAT w keyring ze scope `repo` — działa;
  fine-grained `GH_TOKEN` w `.bashrc` zakomentowany)
- Praca lokalna: serwer `llama-server` na 8080 uruchamiany ręcznie,
  port 18080 zarezerwowany dla zarządzanego serwera z programu