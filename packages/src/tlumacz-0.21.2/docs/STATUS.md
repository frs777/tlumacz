# Agent Translator V2 - Status Projektu

## Koncepcja

V2 to refaktoryzacja oryginalnego projektu `agent-translator` (v1) z architekturą opartą na **ServerManager** - centralnym komponencie zarządzającym cyklem życia serwera llama-server.

**Wersja:** 0.21.0-dev
**Status:** wersja robocza/testowa
**Licencja:** MIT

---

## Architektura V2

```
┌─────────────────────────────────────────────────────────┐
│  MainWindow (GUI)                                        │
│  - Zakładki: Tłumaczenie, API i serwer, Dodatki, Pomoc  │
│  - Oddelegowuje operacje serwera do ServerManager        │
└─────────────────────────────────────────────────────────
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ServerManager (nowy)                                    │
│  - Stan maszyny: IDLE/STARTING/RUNNING/STOPPING         │
│  - Kolejka operacji (zapobiega równoległym operacjom)   │
│  - Automatyczny restart przy błędach                     │
│  - Zarządzanie procesem i portem                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  LlamaServer (z v1)                                      │
│  - Start/stop procesu llama-server                       │
│  - Health check (is_running)                             │
│  - _kill_by_port (czyszczenie orphaned processes)        │
└─────────────────────────────────────────────────────────┘
```

### Kluczowe Różnice V1 vs V2

| Cecha | V1 (oryginalny) | V2 (refaktoryzacja) |
|-------|-----------------|---------------------|
| Zarządzanie serwerem | MainWindow bezpośrednio | ServerManager (centralny) |
| Stan serwera | Brak jawnej maszyny stanów | IDLE/STARTING/RUNNING/STOPPING |
| Kolejka operacji | Brak (ryzyko race conditions) | Tak (bezpieczne operacje) |
| Automatyczny restart | Nie | Tak (przy błędach) |
| Thread lifecycle | Podstawowy | Pełny (finished signals) |
| Cloud models | Brak | QComboBox + cloud_models.json |
| Szablony czatu | Auto/chatml | jinja/chatml/translategemma |
| Języki docelowe | Nazwy (Polish, English) | "wykryj do X" (wykryj do pl, wykryj do en) |

---

## ✅ Zrealizowane funkcje

### GUI
- Wybór wejścia/wyjścia i ustawień API
- Tłumaczenie w QThread bez blokowania GUI
- Anulowanie, pasek postępu, log i podgląd
- Trwały `config.json` z walidacją i backupami
- Zakładki: Tłumaczenie / API i serwer / Dodatki / Pomoc
- Motywy system/light/dark
- Własny prompt systemowy
- Stoper tłumaczenia
- Pomoc PL/EN z tooltipami i tabelą parametrów
- Checkbox "Czyść cache po tłumaczeniu" — domyślnie włączony
- **Inteligentny przycisk serwera** (4 stany: restart/stop/start/info)
- **QComboBox modeli** — cloud models + LOCAL + ręczny
- **QComboBox szablonów czatu** — jinja/chatml/translategemma
- **Języki "wykryj do X"** — automatyczna detekcja języka źródłowego
- **Auto-select skill** — odznacza poprzednie, zaznacza pasujący do pliku

### Zarządzany llama-server
`tlumacz/server.py` zarządza procesem `llama-server`, ścieżką GGUF, portem i profilem szablonu rozmowy.

**Funkcje:**
- Autofallback `jinja`/`chatml`/`translategemma`
- `_is_port_busy()` — sprawdzenie czy port zajęty
- `_kill_port_occupier()` — zabicie procesu blokującego port
- `_kill_by_port()` — użycie `ss -tlnp` do znalezienia PID
- SIGTERM → SIGKILL eskalacja
- Zapisywanie działającego szablonu w `model_profiles`

### Cloud Translation
- Wczytywanie `cloud_models.json` (projekt/użytkownik/domyślne)
- Automatyczne przełączanie base_url/api_key przy wyborze modelu
- LOCAL pamięta ostatnie ustawienia (`last_local_base_url`, `last_local_api_key`)
- Obsługiwane modele: gemini-3.5-flash, gemini-3.5-flash-lite

### Tłumaczenie i preprocessing
`core.py` obsługuje chunking, prompt, skille, glosariusz, `max_tokens`, ochronę i przywracanie elementów technicznych.

**Format "wykryj do X":**
- System prompt: "Detect the source language and translate ALL text to PL"
- Działa dla wszystkich modeli (nie tylko TranslateGemma)

**Wydajność:**
- Cache tłumaczeń (SQLite) z automatycznym czyszczeniem
- Równoległe tłumaczenie chunków (ThreadPoolExecutor)
- Skalowanie `max_tokens` proporcjonalnie do `chunk_size`
- Statystyki cache w logach (hits/misses)

### Round-trip dokumentów
- **Markdown/TXT:** ✅ działają poprawnie
- **HTML:** ✅ działa poprawnie
- **DOCX:** ✅ round-trip zachowuje strukturę dokumentu
- **ODT:** ✅ round-trip działa (naprawiono bug z `.tail`)
- **EPUB:** ✅ round-trip działa (naprawiono strukturę XHTML)
- **PDF:** ⏳ w trakcie wdrażania — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF, bez OCR)

### Testy
- **102 testy jednostkowe** — wszystkie przechodzą
- Testy ServerManager (stan, kolejka, restart)
- Testy GUI (offscreen)
- Testy formatów: config, profile modeli, skille, preprocessing, ekstrakcja, round-trip DOCX/ODT/EPUB, serwer, cache

---

## 📊 Wyniki testów modeli

**Data:** 3 września 2026
**Szczegółowy raport:** `jakosc_tlumaczenia_v0.20.0.md`

| Model | Tryb | Czas | Jakość | Status |
|-------|------|------|--------|--------|
| Hy-MT2-1.8B-Q4_K_S | GPU | 4:15 | 70% | ❌ Ucinanie |
| Hy-MT2-7B-Q4_K_M + glos | GPU | 19:05 | 75% | ❌ Dyskwalifikacja (wolny) |
| **TranslateGemma-4b-it.Q4_K_M** | **GPU** | **10:17** | **87%** | ✅ **ZWYCIĘZCA** |
| TranslateGemma-4b-it.Q4_K_M | CPU | 11:31 | 87% | ⚠️ Ucinanie 40% (do zbadania) |
| Salamandra 2B | — | — | — | ❌ Odrzucona |

**Wybrany model:** TranslateGemma-4b-it.Q4_K_M na GPU (87% jakości, 10:17 czas, kompletne tłumaczenie)

**Pipeline Hybrydowy — PORZUCONY** (2 września 2026):
- Działał poprawnie tylko dla Markdown (~2 min, ~99.7% jakości)
- Dla ODT/DOCX generował śmieci: powtarzający się tekst, wyciek promptów
- Wniosek: nie ma sensu utrzymywać funkcji hybrydowej tylko dla Markdown

---

## 🚧 Do Zrobienia

### W trakcie
1. **PDF round-trip** — tłumaczenie tekstowe z zachowaniem układu (PyMuPDF)
2. **Stabilizacja przed wydaniem** — niezawodne tłumaczenie wszystkich formatów
3. **Pomoc w GUI → i18n** — przenieść treść Pomocy do systemu i18n
4. **Dokumentacja README PL/EN** — zmodyfikować do wersji v2 (0.21.0)

### Planowane
5. **OCR dla skanów PDF** — architektura przygotowana
6. **Detekcja przez próbę modelu** — mikro-zapytanie wykrywające EOS/tryb myślenia
7. **Pełna edycja config.json przez GUI** — przycisk Zapisz + autozapis
8. **Format plików tłumaczeń** — test kompletności kluczy i18n
9. **Automatyczna synchronizacja repo** — skrypt po buildzie
10. **Ikona repo / social preview** — og-image dla GitHub

### Przed publikacją
11. **Aktualizacja URL w PKGBUILD** — zweryfikować przed publikacją AUR

---

## 📋 Lista Plików

### Zaimplementowane w V2

```
tlumacz/
├── server.py                  # ✅ Zaktualizowany: _kill_by_port, _is_port_busy, translategemma mapping
├── core.py                    # ✅ Zaktualizowany: "wykryj do X" format
├── qt_gui/
│   ├── main_window.py         # ✅ Zaktualizowany: ServerManager, QComboBox, języki, skille
│   ├── worker.py              # ✅ Zaktualizowany: ServerManager bug fixes
│   └── config.py              # ✅ Zaktualizowany: CLOUD_MODELS_CONFIG, last_local_*
└── i18n.py                    # ✅ Zaktualizowany: chat_jinja, chat_translategemma
```

### Dokumentacja

```
docs/
├── STATUS.md                  # ✅ Ten plik
├── TODO.md                    # ✅ Zaktualizowany
├── ADR-001-server-manager-architecture.md  # ✅ Architecture Decision Record
└── DEBUG_QT.md                # ✅ Zaktualizowany
```

---

## 🔧 Instrukcja Budowania

```bash
# Instalacja w trybie deweloperskim
cd /home/frs/Projekty/agent-translator-v2
pip install -e .

# Uruchomienie GUI
tlumacz

# Testy
pytest tests/ -v

# Testy GUI (offscreen)
QT_QPA_PLATFORM=offscreen pytest tests/test_main_window.py -v
```

---

##  Migracja z V1

V2 jest **kompatybilny wstecznie** z konfiguracją v1 (`~/.config/tlumacz/config.json`).

1. Skopiuj konfigurację: `cp ~/.config/tlumacz/config.json ~/.config/tlumacz/config.json.bak`
2. Zainstaluj v2: `pip install -e .`
3. Uruchom: `tlumacz`
4. Sprawdź ustawienia w zakładce "API i serwer"

**Uwaga:** V2 ma dodatkowy komponent `ServerManager` który zarządza serwerem. Jeśli masz problemy, wyłącz "Uruchamiaj serwer razem z programem" i używaj przycisku "Uruchom serwer" ręcznie.

---

**Ostatnia aktualizacja:** 2026-09-05
**Wersja:** 0.21.0-dev
**Status:** Wersja robocza/testowa — wszystkie główne zadania zakończone
