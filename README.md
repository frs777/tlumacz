# Tłumacz

> [Polski (PL)](README_pl.md) · [English (EN)](README.en.md)

**Narzędzie do tłumaczenia dokumentów oparte na AI z interfejsem graficznym Qt (PySide6)**

Tłumacz pliki Markdown, TXT, HTML, PDF, DOCX, ODT i EPUB na polski (lub inny język) przy użyciu dowolnego API zgodnego z OpenAI — lokalnego serwera llama.cpp/Ollama lub chmurowych modeli Gemini.

> [!WARNING]
> **⚠️ Wczesna wersja rozwojowa — nie jest gotowa do użytku produkcyjnego.**
> 
> Tłumacz znajduje się w fazie aktywnego rozwoju (v0.31.1). Aplikacja może zawierać błędy,
> a jakość tłumaczenia zależy od użytego modelu LLM. **Nie zalecamy używania w środowisku
> produkcyjnym ani do tłumaczeń krytycznych dokumentów.**
> 
> Obecnie najlepsze wyniki daje **TranslateGemma-4b** (~87% jakości). Słabsze modele (poniżej 7B
> parametrów) mogą generować niekompletne tłumaczenia, halucynacje i artefakty — szczególnie
> w formatach binarnych (DOCX, ODT, EPUB, PDF).
> 
> Jeśli chcesz przetestować aplikację, zgłaszaj błędy przez [Issues](https://github.com/frs777/tlumacz/issues).

> **Wersja:** 0.31.1 | **Status:** Wersja robocza/testowa | **Licencja:** MIT

---

## 📦 Pobieranie — paczki binarne

Artefakty wydania `0.31.1` znajdują się w `packages/0.31.1/`.

| System | Format | Artefakt | Status |
|--------|--------|----------|--------|
| **Arch Linux** | `.pkg.tar.zst` | `tlumacz-0.31.1-1-any.pkg.tar.zst` | ✅ zbudowany i dodany do lokalnego repo |
| **Debian/Ubuntu** | `.deb` | `tlumacz_0.31.1-1_all.deb` | ✅ struktura pakietu zweryfikowana |
| **Fedora/RHEL** | `.rpm` | `tlumacz-0.31.1-1.noarch.rpm` | ✅ zbudowany |
| **Fedora/RHEL** | `.src.rpm` | `tlumacz-0.31.1-1.src.rpm` | ✅ zbudowany |
| **Linux x86_64** | `.AppImage` | `tlumacz-0.31.1-x86_64-linuxdeploy.AppImage` | ✅ linuxdeploy + appimagetool |

> Szczegóły budowania, ograniczenia i sumy SHA-256: `packages/0.31.1/BUILD-REPORT.md`, `packages/0.31.1/SHA256SUMS` oraz [dokumentacja pakietowania](docs/technical-docs/packaging-release.md).

### Instalacja z paczek

```bash
# Arch Linux (z lokalnego repo lub paczki)
sudo pacman -U tlumacz-0.31.1-1-any.pkg.tar.zst

# Debian/Ubuntu
sudo dpkg -i tlumacz_0.31.1-1_all.deb

# Fedora/RHEL
sudo dnf install ./tlumacz-0.31.1-1.noarch.rpm

# AppImage (bez instalacji)
chmod +x tlumacz-0.31.1-x86_64-linuxdeploy.AppImage
./tlumacz-0.31.1-x86_64-linuxdeploy.AppImage
```

---

## ✨ Funkcje

### 🖥️ Interfejs graficzny
- **Nowoczesne GUI** zbudowane na PySide6 / Qt Widgets
- **Ciemny motyw** z dołączoną ikoną SVG
- **Zakładki:** Tłumaczenie, API i serwer, Dodatki, Pomoc
- **Motywy:** systemowy, jasny, ciemny
- **Pomoc PL/EN** wbudowana w aplikację

### 📄 Obsługiwane formaty
| Format | Rozszerzenie | Zachowanie formatu |
|--------|--------------|-------------------|
| Markdown | `.md`, `.markdown` | ✅ Zachowane |
| Tekst | `.txt` | ✅ Zachowane |
| HTML | `.html`, `.htm` | ✅ Zachowane (ochrona tagów) |
| PDF | `.pdf` | ⚠️ Tekstowe z zachowaniem układu |
| DOCX | `.docx` | ✅ Round-trip XML |
| ODT | `.odt` | ✅ Round-trip XML |
| EPUB | `.epub` | ✅ Round-trip XHTML |

### 🤖 Cztery backendy tłumaczenia

Program obsługuje **cztery backendy tłumaczenia** z możliwością przełączania w GUI:

1. **llama.cpp** (domyślny, rekomendowany) — lokalny serwer z modelami GGUF
2. **Chmura** — zewnętrzne API (Gemini, OpenAI, etc.)
3. **FastAPI (TranslateGemma)** — lokalny serwer z Transformers (specjalny format z kodami języków)
4. **OpenVINO (TranslateGemma INT8)** — bezpośrednia inferencja lokalna na CPU/GPU/AUTO/MULTI

**Porównanie wydajności (test 2026-09-09, plik tagi.md, skill MkDocs):**

| Backend | Czas | Kompletność | Jakość | Rekomendacja |
|---------|------|-------------|--------|--------------|
| **llama.cpp** | **3:19** ⚡ | 153/152 (100%+) | 🏆 Najlepsza | **✅ Używaj domyślnie** |
| OpenVINO | 4:40 | 148/152 (97%) | ⚠️ Dobra | Dla GPU/ograniczonego RAM |
| FastAPI | >10:00 | ⚠️ Zmienna | ⚠️ Zależy od modelu | Eksperymentalne |
| Chmura | zależy | ✅ Pełna | ✅ Najwyższa | Gdy dostęp do internetu |

**Zarządzanie serwerem:**
- **BackendManager** — centralny zarządca z obsługą Qt signals
- **ServerManager** — zarządca dla llama.cpp (maszyna stanów IDLE/STARTING/RUNNING/STOPPING)
- **FastAPIServerManager** — zarządca dla FastAPI + Transformers
- **OpenVINOBackend** — bezpośrednia inferencja TranslateGemma INT8 bez serwera HTTP
- **Inteligentny przycisk serwera** — 4 stany: restart/stop/start/info
- **Obsługa osieroconych procesów** — automatyczne czyszczenie

### ☁️ Tłumaczenie w chmurze
- **Google Gemini** — gemini-3.5-flash, gemini-3.5-flash-lite
- **OpenAI** — GPT-4, GPT-3.5
- **Inne API** — dowolne zgodne z OpenAI Chat Completions
- **Przełączanie** — szybkie przełączanie między chmurą a lokalnym serwerem
- **Pamięć ustawień** — zapamiętuje ostatnie ustawienia lokalne

### 🌍 Tłumaczenie
- **Format "wykryj do X"** — automatyczna detekcja języka źródłowego
- **10 języków docelowych** — polski, angielski, niemiecki, francuski, hiszpański, włoski, ukraiński, czeski, holenderski, rosyjski
- **Równoległe tłumaczenie** — ThreadPoolExecutor dla wielu fragmentów
- **Cache tłumaczeń** — SQLite z auto-cleanup (>7 dni)
- **Ochrona fragmentów** — kod, URL-e, zmienne są chronione przed tłumaczeniem

### 📚 Dodatki
- **Glosariusz CSV** — wymuś stałe tłumaczenia dla wybranych terminów
- **System skills** — instrukcje dla konkretnych formatów (Markdown, HTML, DOCX, ODT, EPUB)
- **Auto-select skill** — automatyczne zaznaczanie skilla pasującego do pliku
- **Własne skille** — dodawaj własne instrukcje w `~/.config/tlumacz/skills/`

### 🔄 Tłumaczenie w tle
- **QThread + QObject** — tłumaczenie nie blokuje GUI
- **multiprocessing.Process** — izolacja procesu tłumaczenia
- **Kooperatywny cancel** — bezpieczne anulowanie w dowolnym momencie
- **Pasek postępu** — postęp tłumaczenia w czasie rzeczywistym
- **Stoper** — czas trwania tłumaczenia
- **Log na żywo** — komunikaty statusu

---

## 🚀 Szybki start

### Instalacja

```bash
# Ze źródeł (rozwój)
pip install -e .

# Uruchomienie
tlumacz
```

### Arch Linux

```bash
# Z lokalnego repozytorium
sudo pacman -S tlumacz

# Lub zbuduj z PKGBUILD
makepkg -si
```

### Pierwsze tłumaczenie (lokalny serwer)

1. **Uruchom aplikację:** `tlumacz`
2. **Przejdź do zakładki „API i serwer"**
3. **Wskaż plik GGUF** w polu „Plik modelu (GGUF)"
4. **Zaznacz** „Uruchamiaj serwer razem z programem"
5. **Kliknij** „Uruchom serwer"
6. **Wróć do zakładki „Tłumaczenie"**
7. **Wybierz pliki** wejściowy i wyjściowy
8. **Kliknij** „Tłumacz"

### Pierwsze tłumaczenie (chmura)

1. **Uruchom aplikację:** `tlumacz`
2. **Przejdź do zakładki „API i serwer"**
3. **Wybierz model** z combo box (np. `gemini-3.5-flash`)
4. **Wprowadź klucz API** w polu „API key"
5. **Wróć do zakładki „Tłumaczenie"** i rozpocznij

---

## ℹ️ O programie

W zakładce **Pomoc** dostępny jest przycisk **O programie**, który pokazuje nazwę aplikacji, wersję `0.31.1`, krótki opis, obsługiwane backendy i licencję MIT. Wersja jest pobierana centralnie z `tlumacz/version.py`.

## 📖 Dokumentacja

### Podręcznik użytkownika

- [**Podręcznik użytkownika**](docs/technical-docs/user-guide.md) — kompletny przewodnik po instalacji, konfiguracji i używaniu
- [Treść pomocy GUI](docs/technical-docs/help-content.md) — treść wbudowanej pomocy

### Dokumentacja techniczna

- [**Zarządzanie serwerem**](docs/technical-docs/server-management.md) — architektura ServerManager, przycisk restart, llama.cpp
- [**Tłumaczenie w chmurze**](docs/technical-docs/cloud-translation.md) — konfiguracja Gemini, OpenAI, innych API
- [**Modele tłumaczenia**](docs/technical-docs/models.md) — TranslateGemma, porównanie jakości, rekomendacje

### Dla deweloperów

- [Indeks dokumentacji](docs/technical-docs/index.md) — architektura, struktura projektu, konfiguracja
- [STATUS.md](docs/STATUS.md) — aktualny stan projektu
- [TODO.md](docs/TODO.md) — lista zadań
- [CHANGELOG.md](CHANGELOG.md) — dziennik zmian
- [ADR-001](docs/ADR-001-server-manager-architecture.md) — architektura ServerManager

---

## 🏆 Rekomendowane modele

### Najlepsza jakość (lokalny)

**TranslateGemma-4b-it.Q4_K_M** — specjalistyczny model tłumaczeniowy od Google

- **Jakość:** 87%
- **Szybkość:** ~10 minut (dokument 5000 słów, GPU)
- **Wymagania:** 4 GB VRAM
- **Backend:** FastAPI + Transformers (specjalny format z kodami języków)

[Szczegółowy opis →](docs/technical-docs/models.md#translategemma--szczegółowy-opis)

**Uwaga:** TranslateGemma wymaga backendu FastAPI + Transformers. llama.cpp **NIE obsługuje** specjalnego formatu z kodami języków.

### Najlepsza szybkość (chmura)

**gemini-3.5-flash-lite** — najszybszy model chmurowy

- **Jakość:** ~90%
- **Szybkość:** ~2 minuty (dokument 5000 słów)
- **Wymagania:** Brak (chmura)
- **Koszt:** Darmowy (1500 RPM)

### Najlepszy balans

**gemini-3.5-flash** — wysoka jakość w chmurze

- **Jakość:** ~92%
- **Szybkość:** ~3 minuty
- **Koszt:** Darmowy (60 RPM)

---

## ⚙️ Konfiguracja

### Plik konfiguracyjny

Ustawienia w `~/.config/tlumacz/config.json`:

```json
{
  "backend_type": "llama",
  "base_url": "http://127.0.0.1:18080/v1",
  "api_key": "ollama",
  "model": "LOCAL",
  "chunk_size": 4000,
  "temperature": 0.1,
  "target_language": "wykryj do pl",
  "server_port": 18080,
  "server_gguf_path": "/ścieżka/do/model.gguf",
  "server_chat_template": "",
  "auto_start_server": false,
  "cache_clear_after_translation": true
}
```

**Pola backendu:**
- `backend_type`: `"llama"` (domyślny), `"cloud"`, `"fastapi"` lub `"openvino"`
- `server_gguf_path`: ścieżka do pliku GGUF (dla llama.cpp)
- `fastapi_model_path`: ścieżka do katalogu modelu (dla FastAPI)

### Tabela parametrów

| Parametr | Co robi | Zalecana wartość | Dlaczego |
|----------|---------|------------------|----------|
| **Base URL** | Adres serwera API | `http://127.0.0.1:18080/v1` | Serwer musi mówić protokołem OpenAI |
| **API key** | Token `Authorization: Bearer` | `ollama` (lokalny) | Lokalne serwery ignorują klucz |
| **Model** | Nazwa modelu | `local` / `gemini-3.5-flash` | Musi być dostępny na serwerze |
| **Rozmiar bloku** | Fragment tekstu (znaki) | **4000–6000** | Mniejszy = lepszy kontekst; większy = mniej wywołań |
| **Temperatura** | Losowość odpowiedzi | **0.1–0.3** | Niska = wierne tłumaczenie |

---

## 🖥️ Serwer lokalny

### Zarządzany serwer (zalecane)

Tłumacz może automatycznie zarządzać procesem `llama-server`:

1. Wskaż plik GGUF w zakładce „API i serwer"
2. Zaznacz „Uruchamiaj serwer razem z programem"
3. Uruchom aplikację — serwer startuje automatycznie
4. Zamknij aplikację — serwer jest zatrzymywany

### Inteligentny przycisk serwera

Przycisk zmienia etykietę w zależności od stanu:

| Stan serwera | Auto-start | Etykieta | Akcja |
|--------------|------------|----------|-------|
| ✅ Działa | ✅ | **Restart serwera** | Zatrzymaj i uruchom ponownie |
| ✅ Działa | ❌ | **Zatrzymaj serwer** | Tylko zatrzymaj |
| ❌ Zatrzymany | ✅ | **Uruchom serwer** | Uruchom |
| ❌ Zatrzymany | ❌ | **Zaznacz box...** | Pokaż informację |

[Szczegółowy opis →](docs/technical-docs/server-management.md#przycisk-multifunkcyjny-restart-serwera)

### Ręczne uruchomienie

```bash
llama-server \
  -m /ścieżka/do/model.gguf \
  --host 127.0.0.1 \
  --port 18080 \
  --ctx-size 8192 \
  --jinja
```

---

## ☁️ Tłumaczenie w chmurze

### Google Gemini

1. Wybierz model z combo box (np. `gemini-3.5-flash`)
2. Base URL zostanie ustawiony automatycznie
3. Wprowadź klucz API z [Google AI Studio](https://aistudio.google.com/)

| Model | Limit RPM | Koszt |
|-------|-----------|-------|
| gemini-3.5-flash | 60 | Darmowy* |
| gemini-3.5-flash-lite | 1500 | Darmowy* |

### Inne API

Tłumacz działa z dowolnym API zgodnym z OpenAI:
- **OpenAI** — GPT-4, GPT-3.5
- **Groq** — szybkie modele open-source
- **Together AI** — różne modele
- **Azure OpenAI** — enterprise

[Szczegółowy opis →](docs/technical-docs/cloud-translation.md)

---

## 📚 Glosariusz

Plik CSV dwukolumnowy `źródło,tłumaczenie`:

```csv
source,target
API,API
backend,backend
machine learning,uczenie maszynowe
```

**Zalety:**
- Wymusza stałe tłumaczenia dla kluczowych terminów
- Automatyczne filtrowanie — tylko terminy z tekstu źródłowego
- Do 5000 wpisów

---

## 🎯 Skille

Skille to instrukcje dla modelu dopasowane do formatu pliku:

```markdown
---
name: Markdown
formats: md, markdown
---
Zachowaj formatowanie Markdown: nagłówki, listy, bloki kodu, linki.
```

**Wbudowane skille:** Markdown, HTML, DOCX, ODT, EPUB, PDF, Plaintext

**Własne skille:** Dodaj pliki `.md` w `~/.config/tlumacz/skills/`

---

## 🧪 Testy

```bash
# Wszystkie testy
pytest tests/ -v

# Tylko testy GUI (offscreen)
QT_QPA_PLATFORM=offscreen pytest tests/test_main_window.py -v

# Tylko testy cache
pytest tests/test_cache.py -v
```

**Status:** 263 testy — wszystkie przechodzą ✅

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────┐
│  MainWindow (GUI)                                        │
│  - Zakładki: Tłumaczenie, API i serwer, Dodatki, Pomoc  │
│  - ServerManager (centralny zarządca)                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ServerManager                                           │
│  - Stan: IDLE/STARTING/RUNNING/STOPPING                 │
│  - Kolejka operacji (brak race conditions)              │
│  - Obsługa osieroconych procesów                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  LlamaServer / API Chmurowe                              │
│  - llama-server (lokalny)                                │
│  - Gemini / OpenAI / inne (chmura)                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Translator                                              │
│  - Chunking z ochroną sekcji                             │
│  - Równoległe tłumaczenie (ThreadPoolExecutor)           │
│  - Cache (SQLite)                                        │
│  - Round-trip DOCX/ODT/EPUB/PDF                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Wymagania

### Minimalne

- **Python 3.10+**
- **System operacyjny:** Linux (testowano na Arch Linux/KDE Plasma), Windows, macOS
- **RAM:** 4 GB (8 GB zalecane dla modeli 7B+)

### Opcjonalne

- **llama-server** — dla wbudowanego zarządzanego serwera
- **GPU** — zalecane dla modeli lokalnych (Vulkan/CUDA)
- **pandoc** — dla ekstrakcji DOCX
- **poppler-utils** — dla ekstrakcji PDF

### Zależności Python

```
openai>=1.0
PySide6>=6.5
PyMuPDF>=1.24.0
```

---

## 📂 Struktura projektu

```
tlumacz/
├── core.py                # Logika tłumaczenia (bez Qt)
├── cache.py               # Cache tłumaczeń SQLite
├── server.py              # Zarządzany proces llama-server
├── extract.py             # Ekstrakcja tekstu z dokumentów
── preprocess.py          # Preprocessing (protect/restore)
├── glossary.py            # Obsługa słowników CSV
├── skill.py               # System skills
├── pdf_extractor.py       # Ekstrakcja PDF (PyMuPDF)
├── i18n.py                # Lokalizacja PL/EN
├── backend_manager.py     # BackendManager (QObject, 3 backendy)
├── fastapi_server.py      # Serwer FastAPI + Transformers
├── fastapi_manager.py     # FastAPIServerManager
└── qt_gui/
    ├── app.py             # Punkt wejścia
    ├── config.py          # Trwałe ustawienia
    ├── main_window.py     # Główne okno Qt
    ├── worker.py          # QThread workers, ServerManager
    ├── theme.py           # Motywy QSS
    ── resources/         # Motyw QSS + ikona SVG

docs/
├── technical-docs/        # Dokumentacja techniczna
│   ├── index.md
│   ├── user-guide.md
│   ├── server-management.md
│   ├── cloud-translation.md
│   ├── models.md
│   └── help-content.md
└── archive/               # Nieaktualne dokumenty (historyczne)

tests/                     # Testy jednostkowe (263 testy)
```

---

## 🔧 Rozwój

```bash
# Klonowanie
git clone https://github.com/frs777/tlumacz.git
cd tlumacz

# Instalacja deweloperska
pip install -e .

# Uruchomienie
tlumacz

# Testy
pytest tests/ -v

# Headless (bez wyświetlacza)
QT_QPA_PLATFORM=offscreen python -m tlumacz.qt_gui.app
```

---

## 🐛 Znane ograniczenia

- **Jakość tłumaczenia** zależy od użytego modelu
- **PDF** — tłumaczenie tekstowe bez OCR (skany nie są obsługiwane)
- **Skill ODT** — niezgodny z kodem (ODT bez skilla działa poprawnie)
- **Wielojęzyczne dokumenty** — mogą wymagać wzmocnienia promptów
- **TranslateGemma** — wymaga FastAPI + Transformers (llama.cpp nie obsługuje specjalnego formatu)
- **OpenVINO** — wymaga `openvino` + `openvino-genai` oraz modelu TranslateGemma INT8; GPU jest zależne od dostępnego pluginu (np. Intel), z fallbackiem na CPU
- **FastAPI** — wymaga pobrania modelu z HuggingFace (zatwierdzenie od Google)

---

## 📋 Roadmapa

### W trakcie
- [ ] PDF round-trip z zachowaniem układu
- [ ] Stabilizacja przed wydaniem
- [ ] Pomoc w GUI → i18n

### Planowane
- [ ] OCR dla skanów PDF
- [ ] Detekcja szablonu czatu przez próbę modelu
- [ ] Pełna edycja config.json przez GUI
- [ ] Wsparcie LaTeX, reStructuredText, AsciiDoc

---

## 🤝 Wkład

Projekt jest rozwijany przez [frs](https://github.com/frs777).

Bug reporty i propozycje funkcji są mile widziane — otwórz [Issue](https://github.com/frs777/tlumacz/issues).

---

## 📄 Licencja

MIT — zobacz [LICENSE.txt](LICENSE.txt)

---

## 🔗 Linki

- **Repozytorium:** https://github.com/frs777/tlumacz
- **Issues:** https://github.com/frs777/tlumacz/issues
- **Dokumentacja:** [docs/technical-docs/](docs/technical-docs/)

---

<p align="center">
  <strong>Tłumacz</strong> — tłumaczenie dokumentów z AI<br>
  <sub>Wersja 0.31.1 | Licencja MIT | Autor: frs</sub>
</p>
