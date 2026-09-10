# Tłumacz V3 — budowa pakietu Windows EXE

## Stan na 2026-09-10

Wersja aplikacji: **0.31.1**.
Repozytorium: `frs777/tlumacz`, branch `main`.

Aktualny build Windows jest wykonywany natywnie przez GitHub Actions na `windows-latest`.
Do pakowania aplikacji Python/PySide6 używany jest **PyInstaller 6.22.2**.
Python używany w CI: **3.12**.

## Aktualny workflow

Plik: `.github/workflows/build-windows.yml`

Workflow uruchamia się:
- ręcznie przez `workflow_dispatch`,
- automatycznie dla tagów `v*`.

Kroki:
1. checkout repozytorium,
2. Python 3.12 + cache pip,
3. instalacja projektu i zależności testowych,
4. pełny `pytest` z `QT_QPA_PLATFORM=offscreen`,
5. PyInstaller z pliku `build/windows/tlumacz.spec`,
6. smoke-test EXE,
7. SHA256,
8. upload artifactu na GitHub Actions.

Zależności instalowane w CI dla testów/builda: `pyinstaller`, `pytest`, `fastapi`, `uvicorn`.
FastAPI i Uvicorn są obecnie instalowane do testów, ale nie są pakowane do podstawowego EXE.

## Plik PyInstaller

Plik: `build/windows/tlumacz.spec`

Punkt startowy aplikacji: `tlumacz/qt_gui/app.py`.
Do EXE trafiają zasoby Qt (`*.qss`, `*.svg`) oraz wbudowane markdownowe skille z `tlumacz.skills`.

Podstawowy build wyklucza opcjonalne backendy:
- `fastapi`, `uvicorn`,
- `transformers`, `torch`, `accelerate`, `safetensors`,
- `openvino`, `openvino_genai`.

EXE działa jako aplikacja GUI bez konsoli (`console=False`).

## Ostatni zweryfikowany build

Workflow zakończył się sukcesem:
`https://github.com/frs777/tlumacz/actions/runs/34456326653`

Plik: `Tlumacz-0.31.1-windows-x86_64.exe`
Rozmiar: 48 906 171 B (~46,6 MiB)
SHA256: `ca0334bbee4eb8ddc0961e977fc8adff12dfd1a04c911dac421a6c6b718ccca3`

Release:
`v0.31.1`

EXE zostało dodane jako asset do release GitHub.

## Ważne ograniczenie obecnego EXE

Obecny pakiet jest **podstawowym buildem Windows**, a nie kompletnym runtime wszystkich backendów.
Opcjonalne komponenty AI nie są w nim bundlowane.

Docelowo trzeba zmienić architekturę dystrybucji zgodnie z decyzją z 2026-09-10.

## Docelowa koncepcja dystrybucji Windows

Podstawą programu jest lokalne tłumaczenie. Dlatego **llama-server ma być częścią podstawowej instalacji Windows**, a nie opcjonalnym dodatkiem.

Model nie powinien być zaszywany w EXE. Użytkownik ma móc wskazać własny model kompatybilny z llama.cpp, np. TranslateGemma 4B/12B, Qwen lub inny odpowiedni model.

Nie upraszczać GUI do pojedynczego pola `C:\AI\Models\model.gguf`. Należy zachować obecny mechanizm `model_profiles` i rozbudować go tak, aby obsługiwał wybór/profilowanie modeli.

Proponowany podział komponentów:
1. Tłumacz GUI + llama-server — zawsze.
2. Biblioteki podstawowe dokumentów i core — zawsze.
3. FastAPI + Uvicorn — opcjonalnie.
4. Transformers + PyTorch — opcjonalnie.
5. OpenVINO — opcjonalnie.
6. Skille tłumaczeniowe użytkownika — opcjonalnie, synchronizowane z repozytorium GitHub.
7. Glossary/słowniki — opcjonalnie, synchronizowane z repozytorium GitHub.
8. Modele — pobierane osobno przez użytkownika, poza instalatorem.

Preferowany docelowy produkt Windows: instalator `Tlumacz-Setup.exe` z checkboxami komponentów opcjonalnych oraz osobny portable/base EXE.

Opcjonalne zależności Python powinny być instalowane do prywatnego runtime/venv aplikacji, aby nie wymagać modyfikowania systemowego Pythona.

Instalator powinien jasno informować, że modele nie są częścią instalatora i należy dobrać model do sprzętu użytkownika.

## Skill budowania EXE

Pełna kopia używanego skilla znajduje się obok tego dokumentu:
`docs/technical-docs/windows-compiler-skill.md`

Źródło skilla:
`/home/frs/.agents/skills/windows-compiler/SKILL.md`

Najważniejsze zasady skilla dla tego projektu:
- preferować native build na `windows-latest`,
- dla aplikacji Python używać PyInstaller,
- dla GUI stosować `--windowed` / `console=False`,
- używać pliku `.spec` przy bardziej złożonym bundlowaniu,
- jawnie dodawać dane, zasoby i hidden imports,
- wykluczać niepotrzebne moduły, aby ograniczyć rozmiar,
- testować aplikację przed buildem,
- wykonać smoke-test gotowego EXE,
- publikować artifact przez `actions/upload-artifact`,
- dla release używać tagów Git,
- rozważyć code signing przy finalnej dystrybucji,
- instalator można zbudować przez NSIS, Inno Setup lub WiX.

## Następny etap po obejrzeniu GUI

Po dostarczeniu screenshotów GUI należy najpierw porównać aktualny interfejs z powyższą koncepcją.
Następnie sprawdzić implementację `model_profiles`, konfigurację serwera llama oraz istniejące pola ustawień.
Dopiero potem projektować zmiany instalatora, wyboru modeli i komponentów opcjonalnych.

Nie zmieniać teraz GUI ani mechanizmu modeli „w ciemno”.
