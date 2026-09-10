# CHANGELOG — Agent Translator V3

## [0.31.1-dev] — 2026-09-10

### Dodane
- **O programie** — przycisk w zakładce Pomoc otwiera okno z nazwą programu, wersją i podstawowymi informacjami.
- **Centralna wersja aplikacji** — numer `0.31.1` jest przechowywany w `tlumacz/version.py` i używany przez okno „O programie”.

### Dokumentacja
- Zaktualizowano numer wersji w `pyproject.toml` i `QWEN.md`.
- Dodano instrukcję aktualizacji numeru wersji widocznego w oknie „O programie”.

## [0.31.0-dev] — 2026-09-09

### Dodane
- **Testy porównawcze backendów** — llama.cpp vs OpenVINO vs FastAPI
- **Wyniki testów** — llama.cpp + MkDocs = najlepsze rozwiązanie (3:19, 153 linie, 100%+)
- **Raport bugów OpenVINO** — `docs/BUG_OPENVINO_SKILL_INTEGRATION.md`

### Naprawione
- **OpenVINO: brak cleanup po błędzie** — dodano `start_chat()` / `finish_chat()` w `openvino_backend.py`
- **OpenVINO: skill za długi** — przepisano `markdown-tags.md` w stylu mkdocs (20 linii zamiast 89)
- **OpenVINO: strikethrough → podkreślenie** — poprawione przez glosariusz + nowy skill
- **OpenVINO: halucynacja PROT** — naprawiona przez przepisanie skilla

### Zmienione
- **Dokumentacja** — zaktualizowano QWEN.md, README_pl.md, docs/STATUS.md, docs/TODO.md
- **Rekomendacja** — llama.cpp + MkDocs jako domyślny backend dla Markdown

### Wydajność
| Backend | Czas (tagi.md) | Kompletność | Jakość |
|---------|----------------|-------------|--------|
| **llama.cpp** | **3:19** ⚡ | 153/152 (100%+) | 🏆 Najlepsza |
| OpenVINO | 4:40 | 148/152 (97%) | ⚠️ Dobra |
| FastAPI | >10:00 | ⚠️ Zmienna | ⚠️ Eksperymentalne |

---

## [0.30.0] — 2026-09-07

### Dodane
- **Backend OpenVINO** — bezpośrednia inferencja INT8 dla TranslateGemma 4B
- **BackendManager** — centralny zarządca 4 backendów (llama/fastapi/openvino/cloud)
- **GUI** — QComboBox "OpenVINO (TranslateGemma INT8)" + urządzenie (CPU/GPU/AUTO/MULTI)
- **Fallback GPU→CPU** — automatyczne przełączenie gdy GPU niedostępne

### Naprawione
- **23 bugi GUI** — patrz `docs/TODO.md` (sekcja 2026-09-08)
- **OpenVINO: APIConnectionError** — OpenVINO nie łączy się przez HTTP
- **OpenVINO: _clean_output()** — nie ucina wieloliniowych tłumaczeń

### Wydajność
- Ładowanie modelu OpenVINO INT8: ~3s
- Tłumaczenie krótkie (~30 znaków): ~5s
- RAM: ~8 GB

---

**Format:** [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/)
