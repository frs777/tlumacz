# Podsumowanie projektu — Tłumacz

**Data:** 19 sierpnia 2026
**Repozytorium:** https://github.com/frs777/tlumacz (publiczne)
**Wersja:** 0.16.0
**Paczka w moje-repo:** `tlumacz-0.5.1-1-any` (Arch, `/home/frs/RepoArch/x86_64`) — do odświeżenia

---

## Co to jest

Narzędzie do tłumaczenia dokumentów oparte na AI z interfejsem graficznym
**Qt (PySide6)**. Tłumaczy pliki Markdown/tekstowe na wybrany język (domyślnie
polski) przez dowolne API zgodne z OpenAI — w tym przez wbudowany, zarządzany
serwer lokalny `llama-server` (GGUF).

## Zrealizowane funkcje

### Interfejs (Qt GUI, v0.5.0 → v0.12.0)
- Wybór plików wejściowych/wyjściowych, ustawienia API (adres, klucz, model,
  rozmiar fragmentów, temperatura, język docelowy)
- Tłumaczenie w tle (QThread, `worker.py`) — UI nigdy się nie zawiesza;
  anulowanie tłumaczenia, pasek postępu, log na żywo, podgląd wyniku
- Trwałe ustawienia w `~/.config/tlumacz/config.json` + walidacja pliku
  (nieznane pola / złe typy wracają do wartości domyślnych z komunikatem)
- Zakładki: **Tłumaczenie / Ustawienia / Pomoc** (v0.12.0)
- Motyw dzień / noc / system (`theme.py`, QSS Catppuccin, v0.6.0)
- Własny prompt tłumaczenia (`system_prompt`, v0.10.0)
- Pomoc PL/EN wbudowana w GUI z przełącznikiem języka (v0.12.0)

### Zarządzany serwer lokalny (v0.5.1 → v0.17.0)
- `tlumacz/server.py` — `LlamaServer` startuje `llama-server` w tle na
  wydzielonym porcie ze wskazanym plikiem **GGUF**; sprzątanie przez
  `atexit` + SIGTERM/SIGINT
- Alias modelu `local` (`SERVER_MODEL_ALIAS`) — API zawsze adresuje model jako
  `local`; `--jinja` w domyślnej komendzie; `ctx-size 8192` (v0.15.0)
- **Szablon czatu** (`server_chat_template`, v0.16.0): modele z nieparsowalnym
  szablonem jinja (np. `translategemma-4b`) uruchamiane przez
  `--no-jinja --chat-template chatml`
- **Odporność na zmianę modelu** (v0.17.0): autofallback startu — próba
  wybranego szablonu, przy niepowodzeniu automatyczny retry z kolejnymi
  kandydatami (`chatml` / jinja); udany szablon zapamiętywany w
  `model_profiles` (w config.json) pod ścieżką GGUF i używany od razu przy
  następnym starcie
- Wyłączanie trybu „myślenia” modelu: `chat_template_kwargs` z
  `enable_thinking: false` + max_tokens 6000 (v0.15.0, ~5× szybciej dla gemma)

### Preprocessing tłumaczenia (v0.16.0 → v0.17.0, `tlumacz/preprocess.py`)
- **Ochrona kodu/URL** — bloki ```, `` inline i URL-e maskowane placeholderami
  `⟦PROT_n⟧` i przywracane po tłumaczeniu (techniczny content zostaje 1:1)
- **Filtrowanie linii** — linie pasujące do wzorców regex (YAML-metadane:
  `license:`, `author:`, `version:` itd.) kopiowane do wyniku bez tłumaczenia
- **Wzorce per skilla** (v0.17.0): opcjonalne pole `skip_patterns` we
  frontmatterze skilla używane automatycznie dla pasującego formatu; pole
  regex w GUI przeniesione do sekcji „Zaawansowane" (deduplikacja wzorców:
  skilla → domyślne → własne użytkownika)
- **Chunkowanie sekcjami** — tekst dzielony przy nagłówkach Markdown zamiast
  w połowie tabel; małe sekcje grupują się w jeden fragment, split tylko przy
  przepełnieniu (`chunk_size`) lub nagłówku po dużej sekcji
- Czyszczenie przeciekających tokenów końca szablonu (`<|im_end|>`, `</s>`...)

### Ekstrakcja formatów binarnych (v0.17.0, `tlumacz/extract.py`)
- PDF (narzędzie `pdftotext`/poppler, fallback: `pypdf`), DOCX
  (`python-docx`, akapity + tabele), ODT (stdlib: zipfile + XML), EPUB
  (stdlib: zipfile + strip HTML) → tekst w stylu Markdown
- Zależności opcjonalne — czytelny komunikat o braku biblioteki
- `translate_file` automatycznie wyodrębnia tekst przed tłumaczeniem;
  wynik zawsze zapisywany jako Markdown (`.md`); **powrót do formatu
  binarnego przez zewnętrzne narzędzia**: .md → PDF „Drukuj → Zapisz jako PDF",
  .md → DOCX (md2docx / markdown-to-google-doc / markdown-docx), .md → ODT
  (MD2odt / md-to-odt / md2odt) — linki w zakładce Pomoc

### Glosariusz / słownik (v0.7.0)
- `tlumacz/glossary.py` — CSV dwie kolumny, detekcja nagłówka, `#`-prefixy,
  deduplikacja, limit 300 wpisów na prompt (szybki odczyt wielkich słowników)
- GUI: wybór pliku CSV, licznik wpisów, dodawanie par z poziomu programu

### Skille formatów (v0.11.0 → v0.17.0)
- Skille `.md` (frontmatter `name`, `formats`) w `tlumacz/skills/`
  (markdown, plaintext, html, **pdf, docx, odt, epub** — v0.17.0)
  wstrzykiwane do promptu przy pasującym rozszerzeniu
- **`skip_patterns` we frontmatterze** (v0.17.0) — wzorce pomijanych linii
  dla danego formatu, używane automatycznie (skilla Markdown niesie wzorce YAML)
- Własne skille użytkownika w `~/.config/tlumacz/skills/` (nadpisują wbudowane
  o tej samej nazwie), przyciski **Odśwież** / **Importuj skilla** / **Nowy
  skilla** (v0.13/0.14/0.17); **`SKILL_TEMPLATE.md`** — szablon z dokumentacją
  pól frontmatteru, kopiowany przez „Nowy skilla..." (nie wykrywany jako skilla)
- Wybór w GUI (grupa „Skille"), zapis do `enabled_skills`

### Ustawienia i pomoc (v0.17.0)
- **Przywracanie domyślnych** — przycisk „Przywróć domyślne": kopia
  `config.backup-<data>.json`, zapis wartości domyślnych z zachowaniem
  ścieżek (`last_input`, `last_output`, `glossary_path`); uszkodzony
  config.json też jest najpierw backupowany
- **Tooltipy przy wszystkich polach** oraz **tabela parametrów** w zakładce
  Pomoc (co robi / ile ustawić / dlaczego) PL + EN, sekcja o konwersji
  wyniku .md → PDF/DOCX/ODT

### Silnik tłumaczenia (v0.8.0 → v0.16.0)
- `core.py` (bez zależności Qt) — chunking, glosariusz, skille, `max_tokens`,
  wykrywanie czy tekst już jest w języku docelowym (przez prompt, v0.8.0)
- `translate_file` używa potoku: `protect` → `split_segments` → tłumaczenie →
  `restore`, z segmentami `keep` kopiowanymi wprost (v0.16.0)

## Struktura kodu

```
tlumacz/
├── core.py                # Silnik tłumaczenia (bez zależności Qt)
├── glossary.py            # CSV glosariusz (bez zależności Qt)
├── preprocess.py          # Ochrona kodu/URL, filtry linii, chunkowanie sekcjami
├── extract.py             # Ekstrakcja tekstu z PDF/DOCX/ODT/EPUB (bez Qt)
├── server.py              # Zarządzany proces llama-server (bez zależności Qt)
├── skill.py               # Skille formatów (bez zależności Qt)
├── skills/                # Wbudowane skille: markdown, plaintext, html,
│                          #   pdf, docx, odt, epub, SKILL_TEMPLATE.md
└── qt_gui/
    ├── app.py             # Punkt wejścia (main()), start/stop serwera, profile modeli
    ├── config.py          # Trwałe ustawienia + walidacja (config.json)
    ├── main_window.py     # Główne okno Qt Widgets (zakładki)
    ├── worker.py          # Worker QThread do tłumaczenia w tle
    ├── theme.py           # Motywy QSS (system / light / dark)
    └── resources/         # Motyw QSS + ikona SVG
```

## Testy

- `python3 -m pytest tests/` — **79 testów** (glosariusz, config z backupem
  i profilami modeli, skille z `skip_patterns` i szablonem, preprocessing,
  ekstrakcja ODT/EPUB + ścieżki błędów PDF/DOCX, serwer (kolejność szablonów),
  silnik tłumaczenia z formatami binarnymi, GUI smoke offscreen)

## Pakowanie / dystrybucja

- **Wheel PyPI:** `python -m build --wheel` → `dist/tlumacz-<wersja>-py3-none-any.whl`
- **AUR:** gotowy `PKGBUILD` (nazwa `tlumacz`, arch `any`, zależności:
  python, pyside6, python-openai, hicolor-icon-theme) — URL do weryfikacji
- **moje-repo:** paczka w `/home/frs/RepoArch/x86_64` (repo `moje-repo`,
  `SigLevel = Optional TrustAll`) — do odświeżenia przy wydaniu

## Konfiguracja (config.json)

```json
{
  "base_url": "http://127.0.0.1:18080/v1",
  "model": "local",
  "chunk_size": 4000,
  "temperature": 0.1,
  "target_language": "Polish",
  "theme": "system",
  "glossary_path": "/home/frs/Projekty/agent-translator/glossary_full.csv",
  "enabled_skills": ["Markdown", "MkDocs translations"],
  "skip_line_patterns": ["^\\s*---\\s*$", "^\\s*(name|license|author|metadata|version|tags|created|updated)\\s*:"],
  "server_port": 17980,
  "server_gguf_path": "/home/frs/Modele/translategemma-4b-it.Q4_K_M.gguf",
  "server_chat_template": "chatml",
  "auto_start_server": true,
  "model_profiles": {
    "/home/frs/Modele/translategemma-4b-it.Q4_K_M.gguf": {"chat_template": "chatml"}
  }
}
```

Uwaga: lokalny serwer (llama.cpp) **ignoruje** nazwę modelu — zawsze używa
`local`. Modele „myślące” (gemma-4-E4B) wymagają `--jinja` +
`enable_thinking: false`; modele tłumaczeniowe z własnym szablonem jinja
(translategemma-4b) uruchamiane są z `--no-jinja --chat-template chatml`
automatycznie (autofallback + `model_profiles`).

## Historia wersji (git)

| Wersja | Opis |
|--------|------|
| v0.1–0.4 | CLI (TypeScript/Ink) — czat, LLM, narzędzia |
| v0.5.0 | Qt GUI (PySide6), tłumaczenie w tle, ustawienia trwałe |
| v0.5.1 | Zarządzany serwer lokalny, ścieżki wyjściowe z sufiksem języka |
| v0.6.0 | Motywy system / light / dark |
| v0.7.0 | Glosariusz CSV (plik + wpisy z GUI) |
| v0.8.0 | Wykrywanie języka wejściowego (przez prompt) |
| v0.9.0 | Walidacja config.json |
| v0.10.0 | Pola serwera w GUI + własny prompt |
| v0.11.0 | Skille formatów (wstrzykiwanie do promptu) + testy (33) |
| v0.12.0 | Zakładki + pomoc PL/EN w GUI |
| v0.13.0 | Skille użytkownika z `~/.config/tlumacz/skills/` |
| v0.14.0 | Odśwież / import skilla, ukryte pliki w dialogach |
| v0.15.0 | Wsparcie gemma-4-E4B: alias `local`, `--jinja`, `enable_thinking: false`, max_tokens 6000; fix nadpisywania config.json |
| v0.16.0 | `preprocess.py` (ochrona kodu/URL, filtry linii regex, chunkowanie sekcjami), `server_chat_template` (chatml), czyszczenie EOS; testy 49 |
| v0.17.0 | Odporność na modele (autofallback + `model_profiles`), `skip_patterns` w skillach, `SKILL_TEMPLATE.md` + „Nowy skilla", ekstrakcja PDF/DOCX/ODT/EPUB + 4 skille, „Przywróć domyślne" + backup, tooltipy i tabela parametrów w Pomocy; testy 79 |
| v0.17.1 | Fix: tłumaczenie dokumentów dwujęzycznych (prompt jawnie nakazuje tłumaczyć wszystkie obcojęzyczne fragmenty); skalowanie okna do ekranu + scrollowane ustawienia; testy 80 |
| v0.17.2 | Fix: ekstrakcja DOCX bez python-docx (fallback pandoc, ostatecznie LibreOffice) — działa w venv bez instalowania pakietów; testy 81 |

## Plan (do_zrobienia.md)

Zob. [do_zrobienia.md](do_zrobienia.md) — najważniejsze pozycje:
- Pełna edycja config.json przez GUI (przycisk Zapisz + autozapis)
- Lista modeli z serwera (`GET /v1/models`) zamiast pola tekstowego
- **Lokalizacja aplikacji (i18n): PL + EN, łatwe dodawanie kolejnych języków**
- Detekcja przez próbę dla modeli (mikro-zapytanie: EOS / tryb „myślenia")
- OCR dla skanów PDF
- Paczki DEB / RPM / AppImage
- Skrypt automatycznej synchronizacji moje-repo
- Ikona repo / og-image

## Uwagi środowiskowe

- Konto GitHub: `frs777` (classic PAT w keyring ze scope `repo`)
- Praca lokalna: serwer `llama-server` na 8080 uruchamiany ręcznie,
  port 17980 zarządzany przez aplikację
- Testy nowych modeli na mniejszym pliku (~½ rozmiaru docelowego) — nowy
  pipeline (preprocessing + sekcje) skraca liczbę chunków i czas (~20% szybciej
  na translategemma-4b niż gemma-4-E4B, brak GPU w maszynie)
